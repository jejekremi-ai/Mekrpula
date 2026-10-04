import os, re, base64, hashlib
import time
from decimal import Decimal, InvalidOperation
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from solders.message import Message
from solders.hash import Hash
from solders.transaction import Transaction, VersionedTransaction
from core import db, user, uid, now
from hubs import get_hub
from chain import rpc, TOKEN_PROGRAM

router = APIRouter(prefix='/api')
ASSOCIATED = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
SYSTEM = Pubkey.from_string('11111111111111111111111111111111')
MEMO = Pubkey.from_string('MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr')

def exact_payment(result, expected_hash):
    if not result: return False
    meta = result.get('meta')
    if not isinstance(meta, dict) or 'err' not in meta or meta['err'] is not None: return False
    try:
        parsed = VersionedTransaction.from_bytes(base64.b64decode(result['transaction'][0]))
        return hashlib.sha256(bytes(parsed.message)).hexdigest() == expected_hash
    except Exception: return False

async def settle_expired_reservations(token):
    # Request-driven reconciliation, not an in-process timer/background scheduler.
    pending = await db.orders.find({'token': token, 'status': 'pending'}, {'_id': 0}).limit(50).to_list(50)
    if not pending: return
    try: height = await rpc('getBlockHeight', [{'commitment': 'finalized'}])
    except HTTPException: return  # Keep stock reserved until chain state can be established.
    for row in pending:
        if height <= row['last_valid_height']: continue
        if row.get('signature'):
            try:
                status = (await rpc('getSignatureStatuses', [[row['signature']], {'searchTransactionHistory': True}]))['value'][0]
                if status and status.get('err') is None:
                    if status.get('confirmationStatus') != 'finalized': continue
                    result = await rpc('getTransaction', [row['signature'], {'encoding': 'base64', 'commitment': 'finalized', 'maxSupportedTransactionVersion': 0}])
                    if not result: continue
                    if exact_payment(result, row['message_hash']):
                        await db.orders.update_one({'id': row['id'], 'status': 'pending'}, {'$set': {'status': 'paid', 'paid_at': now().isoformat()}})
                        continue
                    # Invalid transactions remain reserved for explicit buyer resolution.
                    continue
            except HTTPException: continue
        changed = await db.orders.update_one({'id': row['id'], 'status': 'pending'}, {'$set': {'status': 'cancelled', 'reason': 'Unsigned or failed payment expired'}})
        if changed.modified_count: await db.listings.update_one({'id': row['listing_id']}, {'$inc': {'quantity': 1}})
class ListingInput(BaseModel):
    name: str = Field(min_length=3, max_length=100)
    image: str = Field(min_length=5, max_length=1500)
    type: Literal['Existing NFT', 'Create NFT', 'Artwork', 'Meme Pack', 'Wallpaper', 'GIF', 'T-shirt', 'Hoodie', 'Poster', 'Sticker']
    description: str = Field(min_length=10, max_length=3000)
    price: str = Field(max_length=40)
    quantity: int = Field(ge=1, le=100000)

@router.get('/tokens/{mint}/listings')
async def listings(mint: str, category: str = 'All'):
    await get_hub(mint)
    await settle_expired_reservations(mint)
    query = {'token': mint, 'active': True}
    if category != 'All': query['category'] = category
    return await db.listings.find(query, {'_id': 0}).sort('created_at', -1).to_list(100)

@router.post('/tokens/{mint}/listings')
async def create_listing(mint: str, body: ListingInput, wallet: str = Depends(user)):
    hub = await get_hub(mint)
    if 'NFT' in body.type: raise HTTPException(409, 'NFT listing and minting require durable storage and a configured atomic NFT exchange. No asset has been moved.')
    if hub['program'] != TOKEN_PROGRAM: raise HTTPException(409, 'Market payments currently support standard SPL tokens only. Token-2022 transfer extensions need additional validation.')
    try:
        price = Decimal(body.price)
        units = price * (10 ** hub['decimals'])
        if not price.is_finite() or price <= 0 or units != units.to_integral_value() or units >= 2**64: raise ValueError()
    except (ValueError, InvalidOperation): raise HTTPException(422, f'Enter a positive price with at most {hub["decimals"]} decimal places.')
    if not body.image.startswith(os.environ['APP_ORIGIN'] + '/api/images/'): raise HTTPException(422, 'Upload an item image to MART first.')
    doc = {**body.model_dump(), 'id': uid(), 'token': mint, 'symbol': hub['symbol'], 'seller': wallet, 'price_units': str(int(units)), 'category': 'Physical' if body.type in ['T-shirt', 'Hoodie', 'Poster', 'Sticker'] else 'Artwork', 'active': True, 'created_at': now().isoformat()}
    await db.listings.insert_one(dict(doc)); return doc

@router.delete('/listings/{listing_id}')
async def remove_listing(listing_id: str, wallet: str = Depends(user)):
    result = await db.listings.update_one({'id': listing_id, 'seller': wallet}, {'$set': {'active': False}})
    if not result.matched_count: raise HTTPException(404, 'Your listing was not found.')
    return {'ok': True}

class OrderInput(BaseModel):
    listing_id: str
    delivery: str = Field(min_length=5, max_length=1000)

def ata(owner, mint):
    return Pubkey.find_program_address([bytes(owner), bytes(Pubkey.from_string(TOKEN_PROGRAM)), bytes(mint)], ASSOCIATED)[0]

@router.post('/orders')
async def order(body: OrderInput, wallet: str = Depends(user)):
    item = await db.listings.find_one({'id': body.listing_id, 'active': True}, {'_id': 0})
    if not item: raise HTTPException(404, 'Listing not found.')
    if item['seller'] == wallet: raise HTTPException(400, 'You cannot purchase your own listing.')
    if item['quantity'] < 1:
        await settle_expired_reservations(item['token'])
        item = await db.listings.find_one({'id': body.listing_id, 'active': True}, {'_id': 0})
        if not item or item['quantity'] < 1: raise HTTPException(409, 'This item is sold out.')
    hub = await get_hub(item['token'])
    latest = (await rpc('getLatestBlockhash', [{'commitment': 'confirmed'}]))['value']
    buyer, seller, mint, program = map(Pubkey.from_string, [wallet, item['seller'], item['token'], TOKEN_PROGRAM])
    source, dest = ata(buyer, mint), ata(seller, mint)
    order_id = uid()
    # Idempotent ATA creation and TransferChecked. Seller receives funds directly.
    create_ata = Instruction(ASSOCIATED, bytes([1]), [AccountMeta(buyer, True, True), AccountMeta(dest, False, True), AccountMeta(seller, False, False), AccountMeta(mint, False, False), AccountMeta(SYSTEM, False, False), AccountMeta(program, False, False)])
    transfer = Instruction(program, bytes([12]) + int(item['price_units']).to_bytes(8, 'little') + bytes([hub['decimals']]), [AccountMeta(source, False, True), AccountMeta(mint, False, False), AccountMeta(dest, False, True), AccountMeta(buyer, True, False)])
    memo = Instruction(MEMO, f'MART:{order_id}'.encode(), [AccountMeta(buyer, True, False)])
    message = Message.new_with_blockhash([create_ata, transfer, memo], buyer, Hash.from_string(latest['blockhash']))
    transaction = Transaction.new_unsigned(message)
    item = await db.listings.find_one_and_update({'id': item['id'], 'quantity': {'$gt': 0}, 'active': True}, {'$inc': {'quantity': -1}}, projection={'_id': 0}, return_document=ReturnDocument.AFTER)
    if not item: raise HTTPException(409, 'The last item was just reserved.')
    doc = {'id': order_id, 'listing_id': item['id'], 'item_name': item['name'], 'image': item['image'], 'token': item['token'], 'symbol': item['symbol'], 'price': item['price'], 'buyer': wallet, 'seller': item['seller'], 'delivery': body.delivery, 'status': 'pending', 'last_valid_height': latest['lastValidBlockHeight'], 'message_hash': hashlib.sha256(bytes(message)).hexdigest(), 'transaction': base64.b64encode(bytes(transaction)).decode(), 'created_at': now().isoformat()}
    await db.orders.insert_one(dict(doc)); return doc

class SignatureInput(BaseModel):
    signature: str = Field(min_length=64, max_length=100)

@router.post('/orders/{order_id}/submit')
async def mark_submitted(order_id: str, body: SignatureInput, wallet: str = Depends(user)):
    row = await db.orders.find_one({'id': order_id, 'buyer': wallet}, {'_id': 0})
    if not row: raise HTTPException(404, 'Order not found.')
    if row['status'] in ['paid', 'fulfilled']: return row
    if row['status'] != 'pending': raise HTTPException(409, 'This order cannot be paid.')
    if row.get('signature') and row['signature'] != body.signature: raise HTTPException(409, 'A different transaction is already attached.')
    try:
        await db.orders.update_one({'id': order_id, 'status': 'pending'}, {'$set': {'signature': body.signature}})
    except DuplicateKeyError: raise HTTPException(409, 'This transaction belongs to another order.')
    return {'ok': True}

@router.post('/orders/{order_id}/verify')
async def verify_payment(order_id: str, wallet: str = Depends(user)):
    row = await db.orders.find_one({'id': order_id, 'buyer': wallet}, {'_id': 0})
    if not row: raise HTTPException(404, 'Order not found.')
    if row['status'] in ['paid', 'fulfilled']: return row
    if row['status'] != 'pending' or not row.get('signature'): raise HTTPException(409, 'No submitted payment for this order.')
    tx = await rpc('getTransaction', [row['signature'], {'encoding': 'base64', 'commitment': 'finalized', 'maxSupportedTransactionVersion': 0}])
    if not tx: raise HTTPException(409, 'Payment is not finalized yet. Check again shortly from My Purchases.')
    if tx['meta']['err'] is not None: raise HTTPException(409, 'The transaction failed on-chain. No successful payment was recorded.')
    if not exact_payment(tx, row['message_hash']): raise HTTPException(422, 'Payment does not match the exact order transaction.')
    await db.orders.update_one({'id': order_id, 'status': 'pending'}, {'$set': {'status': 'paid', 'paid_at': now().isoformat()}})
    return await db.orders.find_one({'id': order_id}, {'_id': 0})

@router.post('/orders/{order_id}/cancel')
async def cancel(order_id: str, wallet: str = Depends(user)):
    row = await db.orders.find_one({'id': order_id, 'buyer': wallet}, {'_id': 0})
    if not row or row['status'] != 'pending': raise HTTPException(409, 'Order cannot be cancelled.')
    height = await rpc('getBlockHeight', [{'commitment': 'finalized'}])
    if height <= row['last_valid_height']: raise HTTPException(409, 'Wait for the unsigned payment to expire before releasing this item (about 90 seconds).')
    if row.get('signature'):
        status = (await rpc('getSignatureStatuses', [[row['signature']], {'searchTransactionHistory': True}]))['value'][0]
        if status and status['err'] is None: raise HTTPException(409, 'This payment was submitted. Verify it instead of cancelling.')
    changed = await db.orders.update_one({'id': order_id, 'status': 'pending'}, {'$set': {'status': 'cancelled'}})
    if changed.modified_count: await db.listings.update_one({'id': row['listing_id']}, {'$inc': {'quantity': 1}})
    return {'ok': True}

class FulfillInput(BaseModel):
    note: str = Field(min_length=5, max_length=2000)

@router.post('/orders/{order_id}/fulfill')
async def fulfill(order_id: str, body: FulfillInput, wallet: str = Depends(user)):
    result = await db.orders.update_one({'id': order_id, 'seller': wallet, 'status': 'paid'}, {'$set': {'status': 'fulfilled', 'fulfillment': body.note}})
    if not result.modified_count: raise HTTPException(409, 'A paid order belonging to you is required.')
    return {'ok': True}