from datetime import timedelta
import os
from typing import Literal
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from pymongo import ReturnDocument
from core import db, now, user
from compute_catalog import UNIT, RATES, FREQUENCIES, catalog, estimate, TARIFF_VERSION
from compute_store import account, context, authorize, event, log, recover_stale
from compute_runner import prepare, execute

router = APIRouter(prefix='/api', tags=['compute'])

class Operation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: str = Field(min_length=8, max_length=80, pattern=r'^[a-zA-Z0-9_-]+$')

class TopUp(Operation):
    amount: int = Field(default=100, ge=1, le=100, strict=True)

class Limits(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    per_run_limit: float = Field(ge=0.01, le=50)
    daily_limit: float = Field(ge=0.01, le=200)
    paused: bool = False

class Schedule(BaseModel):
    model_config = ConfigDict(extra='forbid')
    enabled: bool
    frequency: Literal['hourly', 'every-6-hours', 'daily', 'weekly'] = 'daily'

class RunView(BaseModel):
    model_config = ConfigDict(extra='ignore')
    id: str
    token: str
    model_id: str
    trigger: str
    status: str
    created_at: str
    reserved: int
    charged: int = 0
    output: str = ''
    usage: dict = Field(default_factory=dict)
    sources: list[dict] = Field(default_factory=list)
    error: str | None = None
    finished_at: str | None = None
    snapshot_at: str | None = None
    tariff_version: str | None = None
    mode: str | None = None

class ComputeView(BaseModel):
    token: str
    mode: str
    can_manage: bool
    owner: str | None
    model_id: str
    runnable: bool
    balance: float
    reserved: float
    spent: float
    day_spent: float
    per_run_limit: float
    daily_limit: float
    runs_completed: int
    remaining_daily_runs: int
    active_run: str | None
    manual_completed: bool
    paused: bool
    schedule: dict
    ledger: list[dict]
    activity: list[dict]
    runs: list[RunView]
    tariff_version: str

@router.get('/compute/estimate')
async def budget(model_id: str, frequency: str = 'daily'):
    return estimate(model_id, frequency)

@router.get('/tokens/{mint}/compute', response_model=ComputeView)
async def view(mint: str, authorization: str = Header('')):
    await recover_stale()
    hub, agent, profile = await context(mint)
    acc = await account(mint)
    owner = agent.get('updated_by') if agent else hub.get('claimed_by')
    wallet = None
    if authorization:
        try: wallet = await user(authorization)
        except HTTPException: pass
    runs = await db.compute_runs.find({'token': mint}, {'_id': 0, 'prompt': 0, 'system': 0}).sort('created_at', -1).to_list(20)
    money = {k: acc[k] / UNIT for k in ['balance', 'reserved', 'spent', 'day_spent', 'per_run_limit', 'daily_limit']}
    ledger = [{**item, 'amount': item['amount'] / UNIT, 'reserved': item.get('reserved', 0) / UNIT,
               'released': item.get('released', 0) / UNIT} for item in reversed(acc['ledger'][-50:])]
    return ComputeView(token=mint, mode='creator' if agent or owner else 'community-test', owner=owner,
        can_manage=wallet == owner if owner else os.environ.get('COMPUTE_TEST_MODE') == 'true', model_id=profile['model_id'],
        runnable=profile['model_id'] in RATES and (not agent or 'research' in profile.get('capabilities', [])),
        **money, runs_completed=acc['runs_completed'], remaining_daily_runs=max(0, 5 - acc['day_runs']),
        active_run=acc['active_run'], manual_completed=acc.get('manual_model') == profile['model_id'],
        paused=acc['paused'], schedule={k: v for k, v in acc['schedule'].items() if k != 'authorized_by'},
        ledger=ledger, activity=list(reversed(acc['activity'])), runs=runs, tariff_version=TARIFF_VERSION)

@router.post('/tokens/{mint}/compute/topup', response_model=ComputeView)
async def topup(mint: str, body: TopUp, authorization: str = Header('')):
    await authorize(mint, authorization)
    await account(mint)
    amount = body.amount * UNIT
    entry = {'id': body.request_id, 'at': now().isoformat(), 'kind': 'topup', 'amount': amount}
    result = await db.compute_accounts.update_one({'token': mint, 'ledger.id': {'$ne': body.request_id},
        'funded': {'$lte': 1000 * UNIT - amount}}, {'$inc': {'balance': amount, 'funded': amount},
        '$push': {'ledger': {'$each': [entry], '$slice': -500},
        'activity': {'$each': [event('credit', f'{body.amount} CR kredit uji ditambahkan')], '$slice': -150}}})
    if not result.modified_count:
        acc = await account(mint)
        if not any(x['id'] == body.request_id for x in acc['ledger']):
            raise HTTPException(409, 'Batas total pengisian kredit uji token ini adalah 1.000 CR.')
    return await view(mint, authorization)

@router.patch('/tokens/{mint}/compute/limits', response_model=ComputeView)
async def limits(mint: str, body: Limits, authorization: str = Header('')):
    await authorize(mint, authorization)
    acc = await account(mint)
    if acc['active_run']: raise HTTPException(409, 'Tunggu riset selesai sebelum mengubah batas.')
    if body.per_run_limit > body.daily_limit: raise HTTPException(422, 'Batas per riset tidak boleh melebihi batas harian.')
    changes = {'per_run_limit': round(body.per_run_limit * UNIT), 'daily_limit': round(body.daily_limit * UNIT), 'paused': body.paused}
    if body.paused: changes.update({'schedule.enabled': False, 'schedule.next_run_at': None})
    result = await db.compute_accounts.update_one({'token': mint, 'active_run': None}, {'$set': changes})
    if not result.matched_count: raise HTTPException(409, 'Riset baru dimulai. Coba lagi setelah selesai.')
    await log(mint, 'settings', 'Batas biaya diperbarui' + (' · Agent dijeda' if body.paused else ''))
    return await view(mint, authorization)

@router.post('/tokens/{mint}/compute/runs', response_model=RunView, status_code=202)
async def run(mint: str, body: Operation, tasks: BackgroundTasks, authorization: str = Header('')):
    await authorize(mint, authorization)
    await recover_stale()
    result, fresh = await prepare(mint, body.request_id)
    if fresh: tasks.add_task(execute, result['id'])
    return result

@router.get('/tokens/{mint}/compute/runs/{run_id}', response_model=RunView)
async def get_run(mint: str, run_id: str):
    result = await db.compute_runs.find_one({'token': mint, 'id': run_id}, {'_id': 0, 'prompt': 0, 'system': 0})
    if not result: raise HTTPException(404, 'Riset tidak ditemukan untuk token ini.')
    return result

@router.patch('/tokens/{mint}/compute/schedule', response_model=ComputeView)
async def schedule(mint: str, body: Schedule, authorization: str = Header('')):
    operator = await authorize(mint, authorization)
    acc = await account(mint)
    _, agent, profile = await context(mint)
    if body.enabled:
        if acc.get('manual_model') != profile['model_id']:
            raise HTTPException(409, 'Jalankan satu riset manual yang berhasil dengan model ini terlebih dahulu.')
        if acc['paused'] or not acc['balance']: raise HTTPException(409, 'Agent harus aktif dan memiliki kredit sebelum jadwal diaktifkan.')
        if profile['model_id'] not in RATES: raise HTTPException(409, 'Model belum terhubung.')
    start = now() + timedelta(hours=FREQUENCIES[body.frequency])
    value = {**body.model_dump(), 'next_run_at': start.isoformat() if body.enabled else None,
             'authorized_by': operator, 'expires_at': (now() + timedelta(days=7, hours=1)).isoformat()}
    await db.compute_accounts.update_one({'token': mint}, {'$set': {'schedule': value}})
    await log(mint, 'schedule', f'Jadwal {body.frequency} ' + ('diaktifkan · masa uji 7 hari' if body.enabled else 'dijeda'))
    return await view(mint, authorization)