"""Read-only token agent breakdown and trusted creator-form attachment."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError
from core import db, user, now, uid
from hubs import get_hub
from chain import current_authority
from agent_schema import AgentProfile, PublicAgentProfile, MODELS, CAPABILITIES

router = APIRouter(prefix='/api', tags=['agent-profiles'])

class Activity(BaseModel):
    id: str
    title: str
    at: str
    kind: str

class AgentView(BaseModel):
    profile: PublicAgentProfile | None = None
    model: dict | None = None
    published: bool = False
    execution_enabled: bool = False
    source: str | None = None
    updated_at: str | None = None
    activity: list[Activity] = Field(default_factory=list)
    ecosystem: dict[str, int] = Field(default_factory=dict)
    compute: dict = Field(default_factory=lambda: {'status': 'not_connected', 'credits_usd': None, 'spent_usd': None, 'runs': 0})

async def attach_profile(mint, profile: AgentProfile, wallet, source):
    """Called only AFTER authority or exact finalized-launch verification.

    Unique token index + setOnInsert makes confirm retries non-destructive.
    Launch source and wallet must match on a replay; no silent overwrite.
    """
    stamp = now().isoformat()
    title = 'Agent configured at token launch' if source == 'mart-launch' else 'Agent configured by verified token authority'
    doc = {'token': mint, 'profile': profile.model_dump(), 'source': source,
           'updated_by': wallet, 'updated_at': stamp,
           'activity': [Activity(id=uid(), title=title, at=stamp, kind='configuration').model_dump()]}
    try:
        await db.agents.update_one({'token': mint}, {'$setOnInsert': doc}, upsert=True)
    except DuplicateKeyError:
        pass
    stored = await db.agents.find_one({'token': mint}, {'_id': 0})
    if stored['profile'] != profile.model_dump() or stored.get('updated_by') != wallet or stored.get('source') != source:
        raise HTTPException(409, 'This token already has a creator-configured agent. Its configuration cannot be replaced.')

@router.get('/agent/models')
async def models():
    from compute_catalog import catalog
    return {'models': catalog(), 'execution_enabled': True, 'mode': 'internal-test-credits'}

@router.post('/agent/validate', response_model=AgentProfile)
async def validate(body: AgentProfile):
    return body

@router.get('/tokens/{mint}/agent', response_model=AgentView)
async def agent(mint: str):
    await get_hub(mint)
    row = await db.agents.find_one({'token': mint}, {'_id': 0})
    ecosystem = {
        'listings': await db.listings.count_documents({'token': mint, 'active': True}),
        'events': await db.events.count_documents({'token': mint}),
        'posts': await db.posts.count_documents({'token': mint}),
    }
    from compute_store import context, account
    from compute_catalog import RATES, UNIT
    _, _, profile = await context(mint)
    acc = await account(mint)
    public = PublicAgentProfile(**profile)
    return AgentView(profile=public, model=next((m for m in MODELS if public and m['id'] == public.model_id), None),
        published=bool(row), source=row.get('source', 'verified-authority') if row else 'community-test',
        execution_enabled=public.model_id in RATES and not acc['paused'],
        updated_at=row.get('updated_at') if row else None, activity=list(reversed(acc['activity'][-10:])), ecosystem=ecosystem,
        compute={'status': 'running' if acc['active_run'] else 'paused' if acc['paused'] else 'ready',
                 'credits': acc['balance'] / UNIT, 'runs': acc['runs_completed']})

@router.patch('/tokens/{mint}/agent', response_model=AgentView)
async def publish(mint: str, body: AgentProfile, wallet: str = Depends(user)):
    # Compatibility route: no public editor, no mutations after creation.
    hub = await get_hub(mint)
    if hub.get('claimed_by') != wallet:
        raise HTTPException(403, 'Only the verified token authority can configure an agent profile.')
    await current_authority(mint, wallet)
    await attach_profile(mint, body, wallet, 'verified-authority')
    return await agent(mint)