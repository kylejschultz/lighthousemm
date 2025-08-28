from __future__ import annotations
import os
import time
import json
import logging
from typing import Iterator
from guessit import guessit
from sqlalchemy.orm import Session
from lhmm.db.session import SessionLocal
from lhmm.db.models import Library, Disk, Series, MediaItem, MediaFile, LibraryScan
from lhmm.services.tmdb_match import best_movie, best_tv

VIDEO_EXTS = {".mkv", ".mp4", ".avi", ".mov", ".m4v", ".ts", ".webm"}

lg = logging.getLogger("lhmm.scanner")


def _walk_video_files(root: str) -> Iterator[tuple[str, int, int]]:
    for dp, _, fn in os.walk(root):
        for f in fn:
            if os.path.splitext(f)[1].lower() in VIDEO_EXTS:
                abs_path = os.path.join(dp, f)
                try:
                    st = os.stat(abs_path)
                except FileNotFoundError:
                    continue
                yield abs_path, int(st.st_size), int(st.st_mtime)


def _ensure_series(db: Session, tmdb_id: int, name: str, year: int | None) -> Series:
    s = db.query(Series).filter(Series.tmdb_id == tmdb_id).one_or_none()
    if not s:
        s = Series(tmdb_id=tmdb_id, name=name, year=year)
        db.add(s)
        db.flush()
    return s


def _ensure_item(
    db: Session,
    kind: str,
    tmdb_id: int,
    title: str,
    year: int | None,
    series_id: int | None = None,
    season: int | None = None,
    episode: int | None = None,
) -> MediaItem:
    q = db.query(MediaItem).filter(
        MediaItem.kind == kind,
        MediaItem.tmdb_id == tmdb_id,
        MediaItem.series_id.is_(series_id if series_id is not None else None),
        MediaItem.season.is_(season if season is not None else None),
        MediaItem.episode.is_(episode if episode is not None else None),
    )
    item = q.one_or_none()
    if not item:
        item = MediaItem(
            kind=kind,
            tmdb_id=tmdb_id,
            title=title,
            year=year,
            series_id=series_id,
            season=season,
            episode=episode,
        )
        db.add(item)
        db.flush()
    return item


def _link_file(db: Session, library_id: int, item_id: int, rel_path: str, size: int, mtime: int) -> None:
    mf = db.query(MediaFile).filter(
        MediaFile.library_id == library_id,
        MediaFile.rel_path == rel_path,
    ).one_or_none()
    if not mf:
        mf = MediaFile(library_id=library_id, item_id=item_id, rel_path=rel_path, size=size, mtime=mtime, quality_json="{}")
        db.add(mf)
    else:
        mf.item_id = item_id
        mf.size = size
        mf.mtime = mtime


def _lib_root(db: Session, library_id: int) -> str:
    li = db.get(Library, library_id)
    if not li:
        raise RuntimeError("library not found")
    dk = db.get(Disk, li.root_disk_id)
    if not dk:
        raise RuntimeError("disk not found")
    return os.path.join(dk.mount_path, li.root_subdir)


def scan_library(library_id: int) -> dict:
    db = SessionLocal()
    scan = LibraryScan(library_id=library_id, status="running")
    db.add(scan)
    db.flush()
    stats = {"files": 0, "movies": 0, "episodes": 0, "matched": 0, "skipped": 0}
    try:
        root = _lib_root(db, library_id)
        for abs_path, size, mtime in _walk_video_files(root):
            stats["files"] += 1
            rel_path = os.path.relpath(abs_path, root)
            g = guessit(os.path.basename(abs_path))
            try:
                if g.get("type") == "movie":
                    title = g.get("title")
                    year = g.get("year")
                    hit = best_movie(title, year) if title else None
                    if not hit:
                        stats["skipped"] += 1
                        continue
                    item = _ensure_item(
                        db,
                        kind="movie",
                        tmdb_id=int(hit.get("id")),
                        title=(hit.get("title") or title or "").strip(),
                        year=int((hit.get("release_date") or "0000")[:4] or 0) or (int(year) if year else None),
                    )
                    _link_file(db, library_id, item.id, rel_path, size, mtime)
                    stats["movies"] += 1
                    stats["matched"] += 1
                else:
                    title = g.get("title")
                    year = g.get("year")
                    season = g.get("season")
                    episode = g.get("episode")
                    hit = best_tv(title, year) if title else None
                    if not hit or season is None or episode is None:
                        stats["skipped"] += 1
                        continue
                    s = _ensure_series(
                        db,
                        tmdb_id=int(hit.get("id")),
                        name=(hit.get("name") or title or "").strip(),
                        year=int((hit.get("first_air_date") or "0000")[:4] or 0) or (int(year) if year else None),
                    )
                    item = _ensure_item(
                        db,
                        kind="episode",
                        tmdb_id=int(hit.get("id")),
                        title=(hit.get("name") or title or "").strip(),
                        year=s.year,
                        series_id=s.id,
                        season=int(season),
                        episode=int(episode),
                    )
                    _link_file(db, library_id, item.id, rel_path, size, mtime)
                    stats["episodes"] += 1
                    stats["matched"] += 1
            except Exception as e:
                lg.warning({"event": "scan.file.error", "path": abs_path, "err": str(e)})
            if stats["files"] % 50 == 0:
                db.commit()
        db.commit()
        scan.status = "succeeded"
        scan.stats_json = json.dumps(stats)
    except Exception as e:
        scan.status = "failed"
        stats = {**stats, "error": str(e)}
        scan.stats_json = json.dumps(stats)
        db.commit()
        lg.error({"event": "scan.error", "library_id": library_id, "err": str(e)})
        raise
    finally:
        scan.finished_at = int(time.time())
        db.commit()
        db.close()
    lg.info({"event": "scan.end", "library_id": library_id, **stats})
    return stats

