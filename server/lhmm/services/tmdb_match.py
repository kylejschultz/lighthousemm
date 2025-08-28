from __future__ import annotations
from typing import Optional
import httpx
from lhmm.settings import settings

BASE = "https://api.themoviedb.org/3"

def _safe_year(date_str: Optional[str]) -> Optional[int]:
    try:
        if not date_str:
            return None
        return int((date_str or "0000")[:4])
    except Exception:
        return None

def _score_year(y_guess: Optional[int], y_hit: Optional[int]) -> float:
    if not y_guess or not y_hit:
        return 0.0
    d = abs(y_guess - y_hit)
    return max(0.0, 1.0 - min(10, d) / 10.0)

def best_movie(query: str, year: Optional[int]) -> Optional[dict]:
    key = settings.tmdb.api_key
    if not key or not query:
        return None
    with httpx.Client(timeout=10.0) as client:
        r = client.get(f"{BASE}/search/movie", params={"api_key": key, "query": query, "year": year or ""})
        r.raise_for_status()
        results = r.json().get("results", [])
        best = None
        best_s = -1
        for c in results:
            pop = c.get("popularity") or 0
            s = pop + 50 * _score_year(year, _safe_year(c.get("release_date")))
            if s > best_s:
                best, best_s = c, s
        return best

def best_tv(query: str, year: Optional[int]) -> Optional[dict]:
    key = settings.tmdb.api_key
    if not key or not query:
        return None
    with httpx.Client(timeout=10.0) as client:
        r = client.get(f"{BASE}/search/tv", params={"api_key": key, "query": query})
        r.raise_for_status()
        results = r.json().get("results", [])
        best = None
        best_s = -1
        for c in results:
            pop = c.get("popularity") or 0
            s = pop + 50 * _score_year(year, _safe_year(c.get("first_air_date")))
            if s > best_s:
                best, best_s = c, s
        return best

