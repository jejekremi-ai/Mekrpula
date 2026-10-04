import os, time, logging
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from core import db, client, router as core_router
from chain import http
from hubs import router as hubs_router, seed
from social import router as social_router
from market import router as market_router
from launch import router as launch_router
from agents import router as agents_router
from storage import init_storage
from charts import router as charts_router
from compute_routes import router as compute_router
from compute_cron import router as cron_router
from compute_store import recover_stale

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app):
    await db.hubs.create_index('address', unique=True)
    await db.agents.create_index('token', unique=True)
    await db.compute_accounts.create_index('token', unique=True)
    await db.compute_runs.create_index('id', unique=True)
    await db.compute_runs.create_index([('token', 1), ('created_at', -1)])
    await db.compute_dispatches.create_index('id', unique=True)
    await db.compute_daily.create_index('day', unique=True)
    await recover_stale()
    await db.ohlcv_cache.create_index('key', unique=True)
    await db.sessions.create_index('expires', expireAfterSeconds=0)
    await db.nonces.create_index('expires', expireAfterSeconds=0)
    await db.orders.create_index('signature', unique=True, sparse=True)
    for name in ['listings', 'orders', 'events', 'posts', 'images', 'launches']:
        await db[name].create_index('id', unique=True)
    try:
        await init_storage()
    except Exception:
        logging.warning('Image storage initialization unavailable; uploads will retry lazily.')
    await seed()
    yield
    await http.aclose(); client.close()

app = FastAPI(title='MART', lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=os.environ['CORS_ORIGINS'].split(','), allow_credentials=False, allow_methods=['GET', 'POST', 'PATCH', 'DELETE', 'OPTIONS'], allow_headers=['Content-Type', 'Authorization'])
for router in [core_router, hubs_router, social_router, market_router, launch_router, agents_router, charts_router, compute_router, cron_router]: app.include_router(router)
hits = defaultdict(deque)

@app.middleware('http')
async def limits(request: Request, call_next):
    if int(request.headers.get('content-length', '0') or 0) > 5_100_000: return JSONResponse({'detail': 'Request too large.'}, status_code=413)
    if request.method == 'POST':
        key = request.client.host
        stamp = time.monotonic(); bucket = hits[key]
        while bucket and bucket[0] < stamp - 60: bucket.popleft()
        if len(bucket) >= 120: return JSONResponse({'detail': 'Too many requests. Please wait a moment.'}, status_code=429)
        bucket.append(stamp)
    return await call_next(request)

@app.get('/api/health')
async def health(): return {'status': 'ok', 'network': 'solana-mainnet', 'nft_exchange': False, 'nft_storage': False}