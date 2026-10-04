"""Object storage for public token artwork; MongoDB stores references only."""
import os
import asyncio
import httpx
from fastapi import HTTPException

_key = None
_lock = asyncio.Lock()

def storage_url():
    return os.environ['INTEGRATION_PROXY_URL'].rstrip('/') + '/objstore/api/v1/storage'

async def init_storage(force=False):
    global _key
    async with _lock:
        if _key and not force:
            return _key
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(f'{storage_url()}/init', json={'emergent_key': os.environ['EMERGENT_LLM_KEY']})
            response.raise_for_status()
            _key = response.json()['storage_key']
            return _key

async def transfer(method, path, data=None):
    try:
        key = await init_storage()
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.request(method, f'{storage_url()}/objects/{path}', content=data,
                headers={'X-Storage-Key': key, 'Content-Type': 'image/jpeg'})
            if response.status_code == 404:
                key = await init_storage(force=True)
                response = await client.request(method, f'{storage_url()}/objects/{path}', content=data,
                    headers={'X-Storage-Key': key, 'Content-Type': 'image/jpeg'})
            response.raise_for_status()
            return response
    except (httpx.HTTPError, KeyError):
        raise HTTPException(503, 'Image storage is temporarily unavailable. Please try again shortly.')

async def put_image(path, data):
    return (await transfer('PUT', path, data)).json()

async def get_image(path):
    return (await transfer('GET', path)).content