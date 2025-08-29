from __future__ import annotations
import httpx

class SabClient:
    def __init__(self, url: str, api_key: str, timeout=10.0):
        self.url = url.rstrip("/")
        self.key = api_key
        self.timeout = timeout

    async def version(self):
        params = {"mode":"version","output":"json","apikey":self.key}
        async with httpx.AsyncClient(timeout=self.timeout) as cx:
            r = await cx.get(f"{self.url}/api", params=params)
            r.raise_for_status()
            return r.json()

    async def queue(self):
        params = {"mode":"queue","output":"json","apikey":self.key}
        async with httpx.AsyncClient(timeout=self.timeout) as cx:
            r = await cx.get(f"{self.url}/api", params=params)
            r.raise_for_status()
            return r.json()

    async def history(self, start=0, limit=50):
        params = {"mode":"history","start":start,"limit":limit,"output":"json","apikey":self.key}
        async with httpx.AsyncClient(timeout=self.timeout) as cx:
            r = await cx.get(f"{self.url}/api", params=params)
            r.raise_for_status()
            return r.json()

