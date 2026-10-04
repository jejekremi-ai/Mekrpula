import os, secrets, hashlib, base64, io
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi import APIRouter, HTTPException, Header, UploadFile, File, Depends, Response
from pydantic import BaseModel, Field
from nacl.signing import VerifyKey
from solders.pubkey import Pubkey
from PIL import Image, UnidentifiedImageError
import base58
from storage import put_image, get_image

load_dotenv(Path(__file__).parent / '.env')
client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]
router = APIRouter(prefix='/api')
def now(): return datetime.now(timezone.utc)
def uid(): return secrets.token_hex(12)
def address(value):
    try: return str(Pubkey.from_string(value))
    except Exception: raise HTTPException(422, 'Enter a valid Solana address.')

async def user(authorization: str = Header('')):
    token = authorization.removeprefix('Bearer ')
    session = await db.sessions.find_one({'hash': hashlib.sha256(token.encode()).hexdigest(), 'expires': {'$gt': now()}}, {'_id': 0})
    if not session: raise HTTPException(401, 'Connect your wallet and sign in to continue.')
    return session['wallet']

class Challenge(BaseModel):
    wallet: str
class SignedChallenge(BaseModel):
    nonce: str
    signature: str = Field(max_length=150)

@router.post('/auth/challenge')
async def challenge(body: Challenge):
    wallet = address(body.wallet)
    nonce = uid()
    message = f'MART wallet sign-in\nOrigin: {os.environ["APP_ORIGIN"]}\nWallet: {wallet}\nNonce: {nonce}\nIssued: {now().isoformat()}\nThis signature does not authorize a transaction.'
    await db.nonces.insert_one({'nonce': nonce, 'wallet': wallet, 'message': message, 'expires': now() + timedelta(minutes=5)})
    return {'nonce': nonce, 'message': message}

@router.post('/auth/verify')
async def verify(body: SignedChallenge):
    record = await db.nonces.find_one_and_delete({'nonce': body.nonce, 'expires': {'$gt': now()}}, projection={'_id': 0})
    if not record: raise HTTPException(401, 'Sign-in request expired. Please reconnect.')
    try: VerifyKey(base58.b58decode(record['wallet'])).verify(record['message'].encode(), base58.b58decode(body.signature))
    except Exception: raise HTTPException(401, 'Wallet signature could not be verified.')
    token = secrets.token_urlsafe(40)
    await db.sessions.insert_one({'hash': hashlib.sha256(token.encode()).hexdigest(), 'wallet': record['wallet'], 'expires': now() + timedelta(hours=12)})
    return {'token': token, 'wallet': record['wallet']}

@router.post('/auth/logout')
async def logout(authorization: str = Header('')):
    await db.sessions.delete_one({'hash': hashlib.sha256(authorization.removeprefix('Bearer ').encode()).hexdigest()})
    return {'ok': True}

@router.post('/uploads')
async def upload(file: UploadFile = File(...), wallet: str = Depends(user)):
    raw = await file.read(5_000_001)
    if len(raw) > 5_000_000: raise HTTPException(413, 'Please choose an image under 5 MB.')
    try:
        img = Image.open(io.BytesIO(raw))
        if img.width * img.height > 25000000: raise ValueError()
        img.thumbnail((1600, 1600)); output = io.BytesIO()
        img.convert('RGB').save(output, format='JPEG', quality=88)
    except (UnidentifiedImageError, ValueError, OSError): raise HTTPException(422, 'Please upload a valid PNG, JPG or WebP image.')
    image_id = uid()
    result = await put_image(f'mart-agent-hub/uploads/{wallet}/{image_id}.jpg', output.getvalue())
    await db.images.insert_one({'id': image_id, 'wallet': wallet, 'storage_path': result['path'], 'content_type': 'image/jpeg', 'original_filename': file.filename, 'size': result['size'], 'is_deleted': False, 'created_at': now().isoformat()})
    return {'url': f'{os.environ["APP_ORIGIN"]}/api/images/{image_id}'}

@router.get('/images/{image_id}')
async def image(image_id: str):
    row = await db.images.find_one({'id': image_id, 'is_deleted': {'$ne': True}}, {'_id': 0, 'data': 1, 'storage_path': 1})
    if not row: raise HTTPException(404, 'Image not found')
    data = await get_image(row['storage_path']) if row.get('storage_path') else row['data']
    return Response(data, media_type='image/jpeg', headers={'Cache-Control': 'public, max-age=31536000, immutable'})