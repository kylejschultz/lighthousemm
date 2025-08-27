from fastapi import APIRouter, Query
from lhmm.settings import settings
import httpx
import asyncio
from typing import Literal, List, Dict, Any

router = APIRouter(prefix="/tmdb", tags=["tmdb"])

BASE = "https://api.themoviedb.org/3"

async def _search(client: httpx.AsyncClient, path: str, key: str, q: str, page: int) -> List[Dict[str, Any]]:
    r = await client.get(f"{BASE}{path}", params={"api_key": key, "query": q, "page": page})
    r.raise_for_status()
    data = r.json()
    return data.get("results", [])

@router.get("/search")
async def search(
    q: str | None = Query(None, description="query string (alias: 'query')"),
    query: str | None = Query(None, description="alias of 'q'"),
    media_type: Literal["multi", "movie", "tv"] = Query("multi"),
    page: int = Query(1, ge=1, le=100),
):
    qval = (q or query or "").strip()
    if not qval:
        return {"query": qval, "media_type": media_type, "results": []}
    key = settings.tmdb.api_key
    if not key:
        return {"query": qval, "media_type": media_type, "results": []}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            if media_type == "movie":
                mov = await _search(client, "/search/movie", key, qval, page)
                results = [{**it, "media_type": "movie"} for it in mov]
            elif media_type == "tv":
                tv = await _search(client, "/search/tv", key, qval, page)
                results = [{**it, "media_type": "tv"} for it in tv]
            else:
                mov_task = _search(client, "/search/movie", key, qval, page)
                tv_task = _search(client, "/search/tv", key, qval, page)
                mov, tv = await asyncio.gather(mov_task, tv_task)
                merged = (
                    [{**it, "media_type": "movie"} for it in mov]
                    + [{**it, "media_type": "tv"} for it in tv]
                )
                results = sorted(merged, key=lambda x: x.get("popularity", 0), reverse=True)
        return {"query": qval, "media_type": media_type, "results": results}
    except httpx.HTTPError:
        return {"query": qval, "media_type": media_type, "results": []}