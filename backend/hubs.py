import os, time, asyncio
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError
from core import db, user, now, address
from chain import mint_info, metadata, market_data, current_authority, rpc, TOKEN_PROGRAM, TOKEN_2022, http
from agent_schema import AgentProfile

router = APIRouter(prefix='/api')
class AddToken(BaseModel):
    address: str
    agent: AgentProfile | None = None

async def get_hub(mint):
    hub = await db.hubs.find_one({'address': mint}, {'_id': 0})
    if not hub: raise HTTPException(404, 'Token Hub not found.')
    return hub

async def add_hub(mint):
    mint = address(mint)
    existing = await db.hubs.find_one({'address': mint}, {'_id': 0})
    if existing: return existing, False
    info = await mint_info(mint)
    meta, market = await asyncio.gather(metadata(mint), market_data(mint))
    hub = {**market, **meta, 'address': mint, 'name': meta.get('name') or market.get('name') or f'Token {mint[:6]}', 'symbol': (meta.get('symbol') or market.get('symbol') or mint[:5]).upper(), 'decimals': info['decimals'], 'program': info['program'], 'claimed_by': None, 'created_by': None, 'created_at': now().isoformat(), 'description': '', 'pump_url': f'{os.environ["PUMP_WEB_URL"]}/coin/{mint}', 'explorer_url': f'{os.environ["SOLSCAN_URL"]}/token/{mint}', 'dex_url': f'{os.environ["DEX_WEB_URL"]}/solana/{market.get("pair", mint)}'}
    try: await db.hubs.insert_one(dict(hub))
    except DuplicateKeyError: return await get_hub(mint), False
    return hub, True

@router.post('/tokens')
async def add(body: AddToken, authorization: str = Header('')):
    mint = address(body.address.strip())
    wallet = None
    if body.agent is not None:
        wallet = await user(authorization)
        await current_authority(mint, wallet)
        existing = await db.agents.find_one({'token': mint}, {'_id': 0})
        if existing and (existing['profile'] != body.agent.model_dump() or existing.get('updated_by') != wallet or existing.get('source') != 'verified-authority'):
            raise HTTPException(409, 'This token already has an agent. Adding it again will not replace its configuration.')
    hub, created = await add_hub(mint)
    if body.agent is not None:
        from agents import attach_profile
        await attach_profile(mint, body.agent, wallet, 'verified-authority')
    return {'token': hub, 'created': created, 'agent_configured': body.agent is not None}

@router.get('/tokens')
async def tokens(q: str = '', sort: str = 'trending', verified: bool = False):
    import re
    query = {'$or': [{k: {'$regex': re.escape(q[:100]), '$options': 'i'}} for k in ['name', 'symbol', 'address']]} if q else {}
    if verified: query['claimed_by'] = {'$ne': None}
    field = {'trending': 'volume', 'market-cap': 'market_cap', 'newest': 'created_at'}.get(sort, 'volume')
    rows = await db.hubs.find(query, {'_id': 0}).sort(field, -1).to_list(100)
    async def refresh(row):
        if time.time() - row.get('market_updated', 0) > 60:
            market = await market_data(row['address'])
            for key in ['name', 'symbol']: market.pop(key, None)
            if row.get('custom_banner'): market.pop('banner', None)
            if market:
                await db.hubs.update_one({'address': row['address']}, {'$set': market}); row.update(market)
    await asyncio.gather(*(refresh(row) for row in rows[:12]))
    for row in rows:
        row['listing_count'] = await db.listings.count_documents({'token': row['address'], 'active': True})
        row['event_count'] = await db.events.count_documents({'token': row['address']})
    return rows

@router.get('/tokens/{mint}')
async def detail(mint: str):
    hub = await get_hub(mint)
    if time.time() - hub.get('market_updated', 0) > 60:
        market = await market_data(mint)
        for key in ['name', 'symbol']: market.pop(key, None)
        if hub.get('custom_banner'): market.pop('banner', None)
        if market:
            await db.hubs.update_one({'address': mint}, {'$set': market}); hub.update(market)
    return hub

@router.post('/tokens/{mint}/claim')
async def claim(mint: str, wallet: str = Depends(user)):
    hub = await get_hub(mint)
    if hub.get('claimed_by') and hub['claimed_by'] != wallet: raise HTTPException(409, 'This token is already claimed.')
    await current_authority(mint, wallet)
    await db.hubs.update_one({'address': mint}, {'$set': {'claimed_by': wallet, 'claimed_at': now().isoformat()}})
    return await get_hub(mint)

class HubProfile(BaseModel):
    description: str = Field(max_length=2000)
    banner: str = Field(default='', max_length=1500)

@router.patch('/tokens/{mint}')
async def update_hub(mint: str, body: HubProfile, wallet: str = Depends(user)):
    hub = await get_hub(mint)
    if hub.get('claimed_by') != wallet: raise HTTPException(403, 'Only the verified token authority can edit this Hub.')
    await current_authority(mint, wallet)
    await db.hubs.update_one({'address': mint}, {'$set': {**body.model_dump(), 'custom_banner': bool(body.banner)}})
    return await get_hub(mint)

@router.get('/tokens/{mint}/transactions')
async def transactions(mint: str):
    await get_hub(mint)
    rows = await rpc('getSignaturesForAddress', [mint, {'limit': 10}])
    return [{**r, 'url': f'{os.environ["SOLSCAN_URL"]}/tx/{r["signature"]}'} for r in rows]

@router.get('/wallet')
async def dashboard(wallet: str = Depends(user)):
    payload = {'wallet': wallet}
    for collection, field in [('listings', 'seller'), ('orders', 'buyer'), ('events', 'creator'), ('hubs', 'created_by')]:
        payload[collection] = await db[collection].find({field: wallet}, {'_id': 0}).to_list(100)
    payload['sales'] = await db.orders.find({'seller': wallet}, {'_id': 0}).to_list(100)
    try:
        balance, spl, spl22 = await asyncio.gather(rpc('getBalance', [wallet]), rpc('getTokenAccountsByOwner', [wallet, {'programId': TOKEN_PROGRAM}, {'encoding': 'jsonParsed'}]), rpc('getTokenAccountsByOwner', [wallet, {'programId': TOKEN_2022}, {'encoding': 'jsonParsed'}]))
        payload['sol'] = balance['value'] / 1e9
        payload['balances'] = [x['account']['data']['parsed']['info'] for x in spl['value'] + spl22['value'] if int(x['account']['data']['parsed']['info']['tokenAmount']['amount']) > 0]
    except HTTPException as exc: payload['rpc_error'] = exc.detail; payload['balances'] = []; payload['sol'] = None
    return payload

async def seed():
    if await db.hubs.count_documents({}): return
    # Pin canonical mints; ticker/name search can return impersonator tokens.
    for mint in ['9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump', 'DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263', 'EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm', '7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr']:
        try:
            await add_hub(mint)
        except Exception as exc:
            import logging
            logging.warning('Public seed unavailable for %s: %s', mint, str(exc))