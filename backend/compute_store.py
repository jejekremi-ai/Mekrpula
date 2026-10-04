"""Single-document atomic reservations, settlements, and a per-token usage ledger."""
import os
from datetime import timedelta
from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from core import db, now, uid, user
from hubs import get_hub
from chain import current_authority
from compute_catalog import UNIT, catalog

def event(kind, title, run_id=None):
    return {'id': uid(), 'kind': kind, 'title': title, 'at': now().isoformat(), 'run_id': run_id, 'language': 'en'}

async def context(mint):
    hub = await get_hub(mint)
    agent = await db.agents.find_one({'token': mint}, {'_id': 0})
    profile = agent['profile'] if agent else {
        'name': f'{hub["symbol"]} Research', 'role': 'Market analyst',
        'mission': f'Study {hub["name"]} market conditions, follow its community, and develop evidence-based event ideas. Flag risks and gaps in the available data.',
        'model_id': 'claude-sonnet-4-5', 'risk': 'Conservative', 'creativity': 0.3,
        'instructions': '', 'capabilities': ['observe', 'research', 'think', 'strategy', 'monitor']}
    return hub, agent, profile

async def authorize(mint, authorization):
    hub, agent, profile = await context(mint)
    if agent or hub.get('claimed_by'):
        wallet = await user(authorization)
        owner = agent.get('updated_by') if agent else hub.get('claimed_by')
        if owner != wallet:
            raise HTTPException(403, 'Hanya kreator terverifikasi yang dapat mengoperasikan agent resmi token ini.')
        if not agent or agent.get('source') != 'mart-launch':
            await current_authority(mint, wallet)
        return wallet
    if os.environ.get('COMPUTE_TEST_MODE') != 'true':
        raise HTTPException(403, 'Agent komunitas hanya tersedia dalam mode kredit uji.')
    return 'community-test'

async def account(mint):
    await get_hub(mint)
    doc = {'token': mint, 'balance': 0, 'reserved': 0, 'spent': 0, 'funded': 0,
           'per_run_limit': 20 * UNIT, 'daily_limit': 50 * UNIT,
           'day': now().date().isoformat(), 'day_spent': 0, 'day_runs': 0,
           'runs_completed': 0, 'manual_model': None, 'active_run': None,
           'paused': False, 'schedule': {'enabled': False, 'frequency': 'daily', 'next_run_at': None},
           'ledger': [], 'activity': []}
    try:
        await db.compute_accounts.update_one({'token': mint}, {'$setOnInsert': doc}, upsert=True)
    except DuplicateKeyError:
        pass
    await db.compute_accounts.update_one({'token': mint, 'day': {'$ne': doc['day']}},
        {'$set': {'day': doc['day'], 'day_spent': 0, 'day_runs': 0}})
    return await db.compute_accounts.find_one({'token': mint}, {'_id': 0})

async def log(mint, kind, title, run_id=None):
    await db.compute_accounts.update_one({'token': mint}, {'$push': {'activity': {'$each': [event(kind, title, run_id)], '$slice': -150}}})

async def settle(run, cost=0, usage=None, success=False, reason=None):
    """CAS on active_run means retries cannot double debit or refund."""
    cost = min(max(0, cost), run['reserved'])
    entry = {'id': uid(), 'at': now().isoformat(), 'kind': 'usage' if success else 'refund',
             'run_id': run['id'], 'model_id': run['model_id'], 'amount': -cost,
             'reserved': run['reserved'], 'released': run['reserved'] - cost, 'usage': usage or {}}
    updates = {'active_run': None}
    if success and run['trigger'] == 'manual': updates['manual_model'] = run['model_id']
    if not success:
        updates.update({'schedule.enabled': False, 'schedule.next_run_at': None})
    inc = {'balance': run['reserved'] - cost, 'reserved': -run['reserved'], 'spent': cost,
           'day_spent': cost, 'runs_completed': int(success)}
    result = await db.compute_accounts.find_one_and_update({'token': run['token'], 'active_run': run['id']},
        {'$set': updates, '$inc': inc, '$push': {'ledger': {'$each': [entry], '$slice': -500},
        'activity': {'$each': [event('completed' if success else 'failed',
        'Research completed' if success else (reason or 'Research failed; the reservation was released.'), run['id'])], '$slice': -150}}},
        projection={'_id': 0}, return_document=ReturnDocument.AFTER)
    return result is not None

async def recover_stale():
    cutoff = (now() - timedelta(minutes=8)).isoformat()
    async for run in db.compute_runs.find({'status': {'$in': ['queued', 'running']}, 'created_at': {'$lt': cutoff}}, {'_id': 0}):
        await settle(run, reason='Research was interrupted. The reservation was released and the schedule paused.')
        await db.compute_runs.update_one({'id': run['id'], 'status': {'$in': ['queued', 'running']}},
            {'$set': {'status': 'failed', 'error': 'Execution was interrupted. Please run research again.', 'finished_at': now().isoformat(), 'charged': 0}})