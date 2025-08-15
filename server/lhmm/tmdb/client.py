from __future__ import annotations
import os, json, time, asyncio, pathlib
from typing import Any, Dict, List, Optional
import httpx

CACHE_PATH = pathlib.Path(os.environ.get("LHMM_CONFIG_DIR", "/lhmm/config")) / "cache" / "tmdb.json"
BASE_URL = "https://api.themoviedb.org/3"

class TMDBClient:
    def __init__(self, api_key: str):
        if not api_key:
            raise RuntimeError("TMDB API key is not configured")
        self.api_key = api_key
        self._client = httpx.AsyncClient(timeout=20)
        self._img_cfg: Optional[Dict[str, Any]] = None
        self._img_cfg_loaded_at: float = 0.0

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    async def close(self):
        await self._client.aclose()

    async def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        q = {"api_key": self.api_key, **params}
        delay = 0.5
        for _ in range(5):
            r = await self._client.get(f"{BASE_URL}{path}", params=q)
            if r.status_code in (429,) or r.status_code >= 500:
                await asyncio.sleep(delay)
                delay = min(5.0, delay * 2)
                continue
            r.raise_for_status()
            return r.json()
        r.raise_for_status()
        return r.json()

    def _load_cached_img_cfg(self) -> Optional[Dict[str, Any]]:
        try:
            if CACHE_PATH.exists():
                return json.loads(CACHE_PATH.read_text("utf-8"))
        except Exception:
            return None
        return None

    def _save_cached_img_cfg(self, data: Dict[str, Any]) -> None:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(json.dumps(data), encoding="utf-8")

    async def image_config(self) -> Dict[str, Any]:
        now = time.time()
        if self._img_cfg and (now - self._img_cfg_loaded_at) < 7 * 24 * 3600:
            return self._img_cfg
        cached = self._load_cached_img_cfg()
        if cached:
            self._img_cfg = cached
            self._img_cfg_loaded_at = now
            return cached
        data = await self._get("/configuration", {})
        self._img_cfg = data.get("images", {})
        self._img_cfg_loaded_at = now
        self._save_cached_img_cfg(self._img_cfg)
        return self._img_cfg

    async def search(self, q: str) -> Dict[str, List[Dict[str, Any]]]:
        movies = (await self._get("/search/movie", {"query": q})).get("results", [])
        tv = (await self._get("/search/tv", {"query": q})).get("results", [])
        return {"movies": movies, "tv": tv}

    async def movie(self, tmdb_id: int) -> Dict[str, Any]:
        return await self._get(f"/movie/{tmdb_id}", {"append_to_response": "credits"})

    async def tv(self, tmdb_id: int) -> Dict[str, Any]:
        return await self._get(f"/tv/{tmdb_id}", {"append_to_response": "credits"})

def normalize_movie(d: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": d.get("id"),
        "title": d.get("title"),
        "year": (d.get("release_date") or "0000")[:4],
        "overview": d.get("overview"),
        "poster_path": d.get("poster_path"),
        "backdrop_path": d.get("backdrop_path"),
        "genres": [g.get("name") for g in (d.get("genres") or [])],
        "runtime": d.get("runtime"),
        "cast": [
            {"name": c.get("name"), "character": c.get("character"), "profile_path": c.get("profile_path")}
            for c in (d.get("credits", {}).get("cast") or [])[:10]
        ],
    }

def normalize_tv(d: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": d.get("id"),
        "name": d.get("name"),
        "year": (d.get("first_air_date") or "0000")[:4],
        "overview": d.get("overview"),
        "poster_path": d.get("poster_path"),
        "backdrop_path": d.get("backdrop_path"),
        "genres": [g.get("name") for g in (d.get("genres") or [])],
        "episodes": d.get("number_of_episodes"),
        "seasons": d.get("number_of_seasons"),
        "cast": [
            {"name": c.get("name"), "character": c.get("character"), "profile_path": c.get("profile_path")}
            for c in (d.get("credits", {}).get("cast") or [])[:10]
        ],
    }
