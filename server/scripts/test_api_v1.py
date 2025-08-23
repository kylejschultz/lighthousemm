#!/usr/bin/env python3
import os, asyncio, json, sys, tempfile, pathlib

# Ensure a writable sqlite file-based DB for the test
ROOT = pathlib.Path(__file__).resolve().parents[2]
db_path = ROOT / "test_api.sqlite3"
os.environ["LHMM__DB__URL"] = f"sqlite+pysqlite:///{db_path}"

from lhmm.db.base import Base  # noqa: E402
from lhmm.db.session import engine  # noqa: E402
from lhmm.main import app  # noqa: E402
import httpx  # noqa: E402

# Create tables
Base.metadata.create_all(bind=engine)


async def run():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Health
        r = await client.get("/api/v1/healthz")
        assert r.status_code == 200, r.text
        assert r.headers.get("X-Request-ID"), "missing request id header"
        assert r.json().get("ok") is True

        # Initial list disks
        r = await client.get("/api/v1/disks")
        assert r.status_code == 200, r.text
        data = r.json()
        assert data["total"] == 0

        # Create disk
        r = await client.post("/api/v1/disks", json={"name": "d1", "mount_path": "/tmp/mnt1"})
        assert r.status_code == 200, r.text
        disk = r.json()
        disk_id = disk["id"]

        # Get disk
        r = await client.get(f"/api/v1/disks/{disk_id}")
        assert r.status_code == 200, r.text
        assert r.json()["name"] == "d1"

        # Update disk
        r = await client.put(f"/api/v1/disks/{disk_id}", json={"name": "d1b", "mount_path": "/tmp/mnt1"})
        assert r.status_code == 200, r.text
        assert r.json()["name"] == "d1b"

        # Create library
        r = await client.post(
            "/api/v1/libraries",
            json={
                "name": "Lib1",
                "type": "movie",
                "root_disk_id": disk_id,
                "root_subdir": "Movies",
                "settings_json": "{}",
            },
        )
        assert r.status_code == 200, r.text
        lib = r.json()
        lib_id = lib["id"]

        # Attempt invalid library path
        r_bad = await client.post(
            "/api/v1/libraries",
            json={
                "name": "BadLib",
                "type": "tv",
                "root_disk_id": disk_id,
                "root_subdir": "/abs",
                "settings_json": "{}",
            },
        )
        assert r_bad.status_code == 400, (r_bad.status_code, r_bad.text)

        # Try deleting disk while library exists -> expect 400
        r = await client.delete(f"/api/v1/disks/{disk_id}")
        assert r.status_code == 400, r.text

        # Update library
        r = await client.put(
            f"/api/v1/libraries/{lib_id}",
            json={
                "name": "Lib1b",
                "type": "movie",
                "root_disk_id": disk_id,
                "root_subdir": "Movies",
                "settings_json": "{}",
            },
        )
        assert r.status_code == 200, r.text
        assert r.json()["name"] == "Lib1b"

        # Delete library
        r = await client.delete(f"/api/v1/libraries/{lib_id}")
        assert r.status_code == 204, r.text

        # Now delete disk
        r = await client.delete(f"/api/v1/disks/{disk_id}")
        assert r.status_code == 204, r.text

        # Final list
        r = await client.get("/api/v1/disks")
        assert r.status_code == 200, r.text
        assert r.json()["total"] == 0

    print("OK")


if __name__ == "main" or __name__ == "__main__":
    try:
        asyncio.run(run())
    finally:
        # Cleanup test DB file
        try:
            db_path.unlink()
        except Exception:
            pass

