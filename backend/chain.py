import os, base64, struct, time
import httpx
from fastapi import HTTPException
from solders.pubkey import Pubkey
from core import address

TOKEN_PROGRAM = 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'
TOKEN_2022 = 'TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb'
METADATA_PROGRAM = 'metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s'
http = httpx.AsyncClient(timeout=22)

async def rpc(method, params):
    try:
        r = await http.post(os.environ['SOLANA_RPC_URL'], json={'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})
        r.raise_for_status(); data = r.json()
        if data.get('error'): raise ValueError(str(data['error']))
        return data['result']
    except (httpx.HTTPError, ValueError, KeyError): raise HTTPException(503, 'Solana public RPC is temporarily unavailable. Please retry shortly.')

async def mint_info(mint):
    address(mint)
    result = (await rpc('getAccountInfo', [mint, {'encoding': 'jsonParsed', 'commitment': 'confirmed'}]))['value']
    if not result or result.get('owner') not in [TOKEN_PROGRAM, TOKEN_2022] or result.get('data', {}).get('parsed', {}).get('type') != 'mint':
        raise HTTPException(422, 'This address is not an initialized Solana token mint.')
    return {**result['data']['parsed']['info'], 'program': result['owner']}

async def metadata(mint):
    program = Pubkey.from_string(METADATA_PROGRAM)
    pda, _ = Pubkey.find_program_address([b'metadata', bytes(program), bytes(Pubkey.from_string(mint))], program)
    account = (await rpc('getAccountInfo', [str(pda), {'encoding': 'base64'}]))['value']
    if not account: return {}
    if account['owner'] != METADATA_PROGRAM: return {}
    data = base64.b64decode(account['data'][0]); offset = 65
    def string():
        nonlocal offset
        size = struct.unpack_from('<I', data, offset)[0]; offset += 4
        value = data[offset:offset + size].decode('utf-8').strip('\x00').strip(); offset += size
        return value
    try:
        return {'update_authority': str(Pubkey.from_bytes(data[1:33])), 'name': string(), 'symbol': string(), 'metadata_uri': string()}
    except Exception: return {}

async def market_data(mint):
    try:
        r = await http.get(f'{os.environ["DEX_API_URL"]}/token-pairs/v1/solana/{mint}'); r.raise_for_status()
        pairs = [p for p in r.json() if p.get('baseToken', {}).get('address') == mint]
        if not pairs: return {}
        p = max(pairs, key=lambda x: x.get('liquidity', {}).get('usd', 0))
        return {'name': p['baseToken']['name'].strip(), 'symbol': p['baseToken']['symbol'].strip().upper(), 'logo': p.get('info', {}).get('imageUrl', ''), 'banner': p.get('info', {}).get('header', ''), 'price': float(p['priceUsd']) if p.get('priceUsd') else None, 'market_cap': p.get('marketCap'), 'volume': p.get('volume', {}).get('h24'), 'liquidity': p.get('liquidity', {}).get('usd'), 'change': p.get('priceChange', {}).get('h24'), 'pair': p.get('pairAddress'), 'market_updated': time.time(), 'market_source': 'DexScreener', 'socials': p.get('info', {}).get('socials', [])}
    except (httpx.HTTPError, ValueError, TypeError): return {}

async def current_authority(mint, wallet):
    data = await metadata(mint)
    if data.get('update_authority') != wallet: raise HTTPException(403, 'Only the on-chain metadata update authority can claim or manage this token. Renounced or program-controlled authority cannot be claimed here.')