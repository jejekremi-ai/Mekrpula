"""Real, cached USD OHLCV; never synthesize candles when a provider fails."""
import asyncio
import math
import os
import time
from collections import deque
from typing import Literal
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core import db, now
from chain import http
from hubs import get_hub

router = APIRouter(prefix='/api')
_lock = asyncio.Lock()
_calls = deque()
_blocked_until = 0
INTERVALS = {'15m': ('minute', 15), '1h': ('hour', 1), '4h': ('hour', 4), '1d': ('day', 1)}

class Candle(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float
    volume: float

class ChartData(BaseModel):
    mint: str
    pool: str
    interval: str
    source: str = 'GeckoTerminal'
    fetched_at: str
    cached: bool = False
    candles: list[Candle]

async def request_json(path, params=None):
    global _blocked_until
    stamp = time.monotonic()
    while _calls and _calls[0] < stamp - 60:
        _calls.popleft()
    if stamp < _blocked_until or len(_calls) >= 9:
        raise HTTPException(503, 'Chart data is cooling down. Please retry in a minute or open DexScreener.')
    _calls.append(stamp)
    try:
        res = await http.get(f'{os.environ["GECKO_API_URL"]}{path}', params=params, timeout=15)
        if res.status_code == 429:
            _blocked_until = stamp + 60
            raise HTTPException(503, 'Chart provider is rate-limited. Please retry in a minute.')
        if res.status_code == 404:
            return {}
        res.raise_for_status()
        return res.json()
    except (httpx.HTTPError, ValueError):
        raise HTTPException(503, 'Price history is temporarily unavailable. Use Open chart or try again later.')

def normalize_candles(rows):
    candles = {}
    for row in rows:
        try:
            if len(row) != 6:
                continue
            ts, op, hi, lo, close, vol = [float(n) for n in row]
            if not all(math.isfinite(n) for n in [ts, op, hi, lo, close, vol]):
                continue
            if ts <= 0 or min(op, hi, lo, close, vol) < 0 or hi < max(op, close, lo) or lo > min(op, close):
                continue
            candles[int(ts)] = Candle(time=int(ts), open=op, high=hi, low=lo, close=close, volume=vol)
        except (ValueError, TypeError):
            continue
    return [candles[t] for t in sorted(candles)]

@router.get('/tokens/{mint}/ohlcv', response_model=ChartData)
async def chart(mint: str, interval: Literal['15m', '1h', '4h', '1d'] = '1h'):
    hub = await get_hub(mint)
    key = f'{mint}:{interval}'
    async with _lock:
        cached = await db.ohlcv_cache.find_one({'key': key}, {'_id': 0})
        if cached and time.time() - cached['at'] < 60:
            return ChartData(**{**cached['payload'], 'cached': True})
        timeframe, aggregate = INTERVALS[interval]
        params = {'aggregate': aggregate, 'currency': 'usd', 'token': mint, 'limit': 160, 'include_empty_intervals': 'false'}
        pool = hub.get('chart_pool') or hub.get('pair')
        raw = await request_json(f'/networks/solana/pools/{pool}/ohlcv/{timeframe}', params) if pool else {}
        rows = raw.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
        if not rows:
            pools = await request_json(f'/networks/solana/tokens/{mint}/pools')
            choices = sorted(pools.get('data', []), key=lambda p: float(p.get('attributes', {}).get('reserve_in_usd') or 0), reverse=True)
            if not choices:
                raise HTTPException(404, 'No indexed price history for this token yet.')
            pool = choices[0]['attributes']['address']
            raw = await request_json(f'/networks/solana/pools/{pool}/ohlcv/{timeframe}', params)
            rows = raw.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
            await db.hubs.update_one({'address': mint}, {'$set': {'chart_pool': pool}})
        provider_tokens = {v.get('address') for v in raw.get('meta', {}).values() if isinstance(v, dict) and v.get('address')}
        if provider_tokens and mint not in provider_tokens:
            raise HTTPException(502, 'Chart provider returned a different token. Price history was rejected.')
        candles = normalize_candles(rows or [])
        if not candles:
            raise HTTPException(404, 'No candle history is available for this interval yet.')
        payload = ChartData(mint=mint, pool=pool, interval=interval, fetched_at=now().isoformat(), candles=candles)
        await db.ohlcv_cache.update_one({'key': key}, {'$set': {'payload': payload.model_dump(), 'at': time.time()}}, upsert=True)
        return payload