import os, base64, hashlib
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from solders.transaction import VersionedTransaction
from core import db, user, uid, now, address
from chain import http, rpc
from hubs import add_hub
from agent_schema import AgentProfile

router = APIRouter(prefix='/api')
class LaunchInput(BaseModel):
    name: str = Field(min_length=1, max_length=32)
    symbol: str = Field(min_length=1, max_length=10, pattern=r'^[A-Za-z0-9]+$')
    description: str = Field(min_length=10, max_length=1000)
    image: str = Field(max_length=1500)
    banner: str = Field(default='', max_length=1500)
    website: str = Field(default='', max_length=300)
    twitter: str = Field(default='', max_length=300)
    telegram: str = Field(default='', max_length=300)
    mint: str
    amount: float = Field(default=0, ge=0, le=10)
    slippage: int = Field(default=10, ge=1, le=50)
    agent: AgentProfile | None = None

@router.post('/launch/prepare')
async def prepare(body: LaunchInput, wallet: str = Depends(user)):
    address(body.mint)
    if not body.image.startswith(os.environ['APP_ORIGIN'] + '/api/images/'): raise HTTPException(422, 'Upload your token logo first.')
    mid = uid()
    meta = body.model_dump(exclude={'mint', 'amount', 'slippage', 'agent'})
    await db.metadata.insert_one({'id': mid, 'metadata': meta})
    uri = f'{os.environ["APP_ORIGIN"]}/api/metadata/{mid}'
    try:
        result = await http.post(os.environ['PUMP_LOCAL_URL'], json={'publicKey': wallet, 'action': 'create', 'tokenMetadata': {'name': body.name, 'symbol': body.symbol, 'uri': uri}, 'mint': body.mint, 'denominatedInSol': 'true', 'amount': body.amount, 'slippage': body.slippage, 'priorityFee': 0.00001, 'pool': 'pump'})
        if result.status_code != 200: raise ValueError('Pump.fun launch provider declined the request. Please try again later.')
        tx = VersionedTransaction.from_bytes(result.content)
        keys = [str(k) for k in tx.message.account_keys]
        signers = keys[:tx.message.header.num_required_signatures]
        if keys[0] != wallet or set(signers) != {wallet, body.mint}: raise ValueError('Unexpected launch signers. Request was blocked.')
    except Exception as exc: raise HTTPException(502, str(exc)[:250] or 'Launch provider is unavailable.')
    doc = {'id': uid(), 'wallet': wallet, 'mint': body.mint, 'metadata': meta, 'agent_profile': body.agent.model_dump() if body.agent else None, 'message_hash': hashlib.sha256(bytes(tx.message)).hexdigest(), 'created_at': now().isoformat(), 'status': 'prepared'}
    await db.launches.insert_one(dict(doc))
    return {'id': doc['id'], 'transaction': base64.b64encode(result.content).decode(), 'mint': body.mint}

@router.get('/metadata/{mid}')
async def meta(mid: str):
    row = await db.metadata.find_one({'id': mid}, {'_id': 0, 'metadata': 1})
    if not row: raise HTTPException(404, 'Metadata not found.')
    return JSONResponse(row['metadata'], headers={'Cache-Control': 'public, max-age=31536000, immutable'})

class SendInput(BaseModel):
    kind: str = Field(pattern='^(order|launch)$')
    id: str
    transaction: str = Field(max_length=5000)

@router.post('/transactions/send')
async def send(body: SendInput, wallet: str = Depends(user)):
    collection = db.orders if body.kind == 'order' else db.launches
    field = 'buyer' if body.kind == 'order' else 'wallet'
    row = await collection.find_one({'id': body.id, field: wallet}, {'_id': 0})
    if not row or row['status'] not in ['pending', 'prepared']: raise HTTPException(409, 'This transaction is no longer available.')
    try:
        tx = VersionedTransaction.from_bytes(base64.b64decode(body.transaction, validate=True))
        if hashlib.sha256(bytes(tx.message)).hexdigest() != row['message_hash']: raise ValueError()
        tx.verify_and_hash_message()
    except Exception: raise HTTPException(422, 'Signed transaction does not match the approved request.')
    signature = str(tx.signatures[0])
    if row.get('signature') and row['signature'] != signature: raise HTTPException(409, 'A transaction has already been submitted.')
    await collection.update_one({'id': body.id}, {'$set': {'signature': signature}})
    await rpc('sendTransaction', [body.transaction, {'encoding': 'base64', 'skipPreflight': False, 'maxRetries': 3}])
    return {'signature': signature, 'url': f'{os.environ["SOLSCAN_URL"]}/tx/{signature}'}

@router.post('/launch/{launch_id}/confirm')
async def confirm(launch_id: str, wallet: str = Depends(user)):
    row = await db.launches.find_one({'id': launch_id, 'wallet': wallet}, {'_id': 0})
    if not row or not row.get('signature'): raise HTTPException(404, 'Submitted launch not found.')
    result = await rpc('getTransaction', [row['signature'], {'encoding': 'base64', 'commitment': 'finalized', 'maxSupportedTransactionVersion': 0}])
    if not result: raise HTTPException(409, 'Your launch is awaiting finalization. Use Check launch to continue.')
    if result['meta']['err'] is not None: raise HTTPException(409, 'Launch failed on-chain. A Token Hub has not been created.')
    tx = VersionedTransaction.from_bytes(base64.b64decode(result['transaction'][0]))
    if hashlib.sha256(bytes(tx.message)).hexdigest() != row['message_hash']: raise HTTPException(422, 'Unexpected launch transaction.')
    hub, _ = await add_hub(row['mint'])
    await db.hubs.update_one({'address': row['mint']}, {'$set': {'created_by': wallet, 'description': row['metadata']['description'], 'logo': row['metadata']['image'], 'banner': row['metadata']['banner']}})
    if row.get('agent_profile'):
        from agents import attach_profile
        await attach_profile(row['mint'], AgentProfile(**row['agent_profile']), wallet, 'mart-launch')
    await db.launches.update_one({'id': launch_id}, {'$set': {'status': 'confirmed'}})
    return {'address': hub['address']}