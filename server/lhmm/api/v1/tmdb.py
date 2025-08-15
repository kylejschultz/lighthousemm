from fastapi import APIRouter, Query, HTTPException
from lhmm.settings import settings
from lhmm.tmdb.client import TMDBClient, normalize_movie, normalize_tv

router = APIRouter(prefix="/tmdb", tags=["tmdb"])

@router.get("/search")
async def search(q: str = Query(..., min_length=1)):
    if not settings.tmdb.api_key:
        raise HTTPException(status_code=400, detail="TMDB API key not configured")
    client = TMDBClient(settings.tmdb.api_key)
    try:
        return await client.search(q)
    finally:
        await client.close()

@router.get("/title/movie/{tmdb_id}")
async def movie(tmdb_id: int):
    if not settings.tmdb.api_key:
        raise HTTPException(status_code=400, detail="TMDB API key not configured")
    client = TMDBClient(settings.tmdb.api_key)
    try:
        d = await client.movie(tmdb_id)
        return normalize_movie(d)
    finally:
        await client.close()

@router.get("/title/tv/{tmdb_id}")
async def tv(tmdb_id: int):
    if not settings.tmdb.api_key:
        raise HTTPException(status_code=400, detail="TMDB API key not configured")
    client = TMDBClient(settings.tmdb.api_key)
    try:
        d = await client.tv(tmdb_id)
        return normalize_tv(d)
    finally:
        await client.close()
