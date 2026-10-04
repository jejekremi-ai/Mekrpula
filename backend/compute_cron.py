import hmac
import os
from datetime import timedelta
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from core import db, now
from chain import current_authority
from compute_catalog import FREQUENCIES
from compute_store import context, log, recover_stale
from compute_runner import prepare, execute

router = APIRouter(prefix='/api/cron', tags=['scheduled-research'])

async def dispatch_due():
    await recover_stale()
    stamp = now().isoformat()
    rows = await db.compute_accounts.find({'schedule.enabled': True, 'schedule.next_run_at': {'$lte': stamp}}, {'_id': 0}).to_list(100)
    for acc in rows:
        mint, scheduled = acc['token'], acc['schedule']
        next_run = (now() + timedelta(hours=FREQUENCIES[scheduled['frequency']])).isoformat()
        claimed = await db.compute_accounts.find_one_and_update({'token': mint, 'schedule.enabled': True,
            'schedule.next_run_at': scheduled['next_run_at']}, {'$set': {'schedule.next_run_at': next_run}},
            projection={'_id': 0}, return_document=ReturnDocument.AFTER)
        if not claimed: continue
        try:
            if scheduled['expires_at'] < stamp: raise HTTPException(409, 'Masa uji jadwal berakhir. Aktifkan kembali bila diperlukan.')
            hub, agent, _ = await context(mint)
            operator = scheduled['authorized_by']
            owner = agent.get('updated_by') if agent else hub.get('claimed_by')
            if operator == 'community-test':
                if owner or os.environ.get('COMPUTE_TEST_MODE') != 'true': raise HTTPException(403, 'Kontrol token kini dipegang kreator.')
            elif owner != operator: raise HTTPException(403, 'Otorisasi kreator telah berubah.')
            elif not agent or agent.get('source') != 'mart-launch': await current_authority(mint, operator)
            result, fresh = await prepare(mint, f'scheduled-{scheduled["next_run_at"]}', trigger='scheduled')
            if fresh: await execute(result['id'])
        except Exception as exc:
            await db.compute_accounts.update_one({'token': mint}, {'$set': {'schedule.enabled': False, 'schedule.next_run_at': None}})
            await log(mint, 'schedule-paused', getattr(exc, 'detail', 'Jadwal dijeda karena pekerjaan tidak dapat dimulai.'))

@router.post('/research')
async def cron(request: Request, tasks: BackgroundTasks, authorization: str = Header(''), x_webhook_id: str = Header('')):
    # Cron endpoints must ack 2xx immediately; enqueue/background the actual work.
    if not hmac.compare_digest(authorization, 'Bearer ' + os.environ['WEBHOOK_CRON_SECRET']):
        raise HTTPException(401, 'Unauthorized')
    try:
        body = await request.json()
        run_id = x_webhook_id or body.get('run_id')
        if not isinstance(body, dict) or body.get('event') != 'schedule.triggered' or not isinstance(run_id, str) or not 1 <= len(run_id) <= 200:
            raise ValueError()
    except Exception: raise HTTPException(400, 'Invalid schedule envelope')
    try: await db.compute_dispatches.insert_one({'id': run_id, 'received_at': now().isoformat()})
    except DuplicateKeyError: return {'accepted': True, 'duplicate': True}
    tasks.add_task(dispatch_due)
    return {'accepted': True, 'duplicate': False}