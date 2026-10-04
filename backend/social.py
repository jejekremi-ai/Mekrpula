from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from pymongo import ReturnDocument
from core import db, user, uid, now
from hubs import get_hub
from chain import current_authority

router = APIRouter(prefix='/api')
class EventInput(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    image: str = Field(default='', max_length=1500)
    type: Literal['Holder Reward', 'Airdrop', 'Buyback', 'Burn', 'LP Action', 'NFT / Asset Distribution', 'Other']
    description: str = Field(min_length=10, max_length=5000)
    status: Literal['live', 'upcoming', 'past'] = 'upcoming'

@router.get('/events')
async def events(token: str = '', status: str = ''):
    query = {}
    if token: query['token'] = token
    if status: query['status'] = status
    rows = await db.events.find(query, {'_id': 0}).sort('created_at', -1).to_list(100)
    return [{**row, 'type': 'Other' if row.get('type') == 'Treasury Distribution' else row.get('type')} for row in rows]

@router.get('/events/{event_id}')
async def event_detail(event_id: str):
    row = await db.events.find_one({'id': event_id}, {'_id': 0})
    if not row: raise HTTPException(404, 'Event not found.')
    return {**row, 'type': 'Other' if row.get('type') == 'Treasury Distribution' else row.get('type')}

@router.post('/tokens/{mint}/events')
async def create_event(mint: str, body: EventInput, wallet: str = Depends(user)):
    hub = await get_hub(mint)
    if hub.get('claimed_by') != wallet: raise HTTPException(403, 'Claim this token with its verified authority wallet before publishing official events.')
    await current_authority(mint, wallet)
    doc = {**body.model_dump(), 'id': uid(), 'token': mint, 'symbol': hub['symbol'], 'token_name': hub['name'], 'token_logo': hub.get('logo', ''), 'creator': wallet, 'created_at': now().isoformat()}
    await db.events.insert_one(dict(doc)); return doc

class EventStatus(BaseModel):
    status: Literal['live', 'upcoming', 'past']

@router.patch('/events/{event_id}')
async def update_event(event_id: str, body: EventStatus, wallet: str = Depends(user)):
    event = await db.events.find_one({'id': event_id}, {'_id': 0})
    if not event: raise HTTPException(404, 'Event not found.')
    hub = await get_hub(event['token'])
    if hub.get('claimed_by') != wallet: raise HTTPException(403, 'Only the verified token authority can manage this event.')
    await current_authority(event['token'], wallet)
    await db.events.update_one({'id': event_id}, {'$set': {'status': body.status}})
    return await db.events.find_one({'id': event_id}, {'_id': 0})

class PostInput(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    image: str = Field(default='', max_length=1500)

@router.get('/tokens/{mint}/posts')
async def posts(mint: str):
    await get_hub(mint)
    return await db.posts.find({'token': mint}, {'_id': 0}).sort('created_at', -1).to_list(100)

@router.post('/tokens/{mint}/posts')
async def create_post(mint: str, body: PostInput, wallet: str = Depends(user)):
    await get_hub(mint)
    if not body.text.strip(): raise HTTPException(422, 'Write something before posting.')
    doc = {**body.model_dump(), 'id': uid(), 'token': mint, 'author': wallet, 'created_at': now().isoformat(), 'likes': [], 'replies': []}
    await db.posts.insert_one(dict(doc)); return doc

@router.post('/posts/{post_id}/like')
async def like(post_id: str, wallet: str = Depends(user)):
    row = await db.posts.find_one_and_update({'id': post_id}, [{'$set': {'likes': {'$cond': [{'$in': [wallet, '$likes']}, {'$setDifference': ['$likes', [wallet]]}, {'$concatArrays': ['$likes', [wallet]]}]}}}], projection={'_id': 0}, return_document=ReturnDocument.AFTER)
    if not row: raise HTTPException(404, 'Post not found.')
    return row

@router.post('/posts/{post_id}/replies')
async def reply(post_id: str, body: PostInput, wallet: str = Depends(user)):
    if not body.text.strip(): raise HTTPException(422, 'Reply cannot be empty.')
    row = await db.posts.find_one_and_update({'id': post_id}, {'$push': {'replies': {'id': uid(), 'author': wallet, 'text': body.text, 'created_at': now().isoformat()}}}, projection={'_id': 0}, return_document=ReturnDocument.AFTER)
    if not row: raise HTTPException(404, 'Post not found.')
    return row