from fastapi import APIRouter, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from lhmm.db.models import Library, Disk
from lhmm.api.deps import get_db
from lhmm.api.pagination import parse_pagination
from lhmm.api.errors import bad_request, not_found

router = APIRouter(prefix="/libraries", tags=["libraries"])


class LibraryIn(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    type: str = Field(pattern="^(movie|tv)$")
    root_disk_id: int
    root_subdir: str = Field(min_length=1, max_length=256)
    settings_json: str | None = "{}"


class LibraryOut(BaseModel):
    id: int
    name: str
    type: str
    root_disk_id: int
    root_subdir: str
    settings_json: str

    class Config:
        from_attributes = True


def _validate_path_under_disk(db: Session, disk_id: int, root_subdir: str):
    disk = db.get(Disk, disk_id)
    if not disk:
        raise bad_request("Root disk does not exist")
    if root_subdir.startswith("/") or ".." in root_subdir:
        raise bad_request("root_subdir must be a relative directory name")
    return f"{disk.mount_path.rstrip('/')}/{root_subdir}"


@router.get("")
def list_libraries(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    sort: str = Query("name"),
    db: Session = Depends(get_db),
):
    offset, limit = parse_pagination(page, per_page)
    order = Library.name.asc() if sort == "name" else Library.name.desc() if sort == "-name" else Library.id.asc()
    total = db.scalar(select(func.count()).select_from(Library)) or 0
    items = db.execute(select(Library).order_by(order).offset(offset).limit(limit)).scalars().all()
    return {
        "total": total,
        "page": page,
        "per_page": limit,
        "items": [LibraryOut.model_validate(i).model_dump() for i in items],
    }


@router.post("")
def create_library(payload: LibraryIn, db: Session = Depends(get_db)):
    _validate_path_under_disk(db, payload.root_disk_id, payload.root_subdir)
    if db.scalar(select(func.count()).select_from(Library).where(Library.name == payload.name)):
        raise bad_request("Library name already exists")
    li = Library(
        name=payload.name,
        type=payload.type,
        root_disk_id=payload.root_disk_id,
        root_subdir=payload.root_subdir,
        settings_json=payload.settings_json or "{}",
    )
    db.add(li)
    db.flush()
    return LibraryOut.model_validate(li).model_dump()


@router.get("/{library_id}")
def get_library(library_id: int, db: Session = Depends(get_db)):
    li = db.get(Library, library_id)
    if not li:
        raise not_found()
    return LibraryOut.model_validate(li).model_dump()


@router.put("/{library_id}")
def update_library(library_id: int, payload: LibraryIn, db: Session = Depends(get_db)):
    _validate_path_under_disk(db, payload.root_disk_id, payload.root_subdir)
    li = db.get(Library, library_id)
    if not li:
        raise not_found()
    if payload.name != li.name and db.scalar(select(func.count()).select_from(Library).where(Library.name == payload.name)):
        raise bad_request("Library name already exists")
    li.name = payload.name
    li.type = payload.type
    li.root_disk_id = payload.root_disk_id
    li.root_subdir = payload.root_subdir
    li.settings_json = payload.settings_json or "{}"
    db.add(li)
    return LibraryOut.model_validate(li).model_dump()


@router.delete("/{library_id}", status_code=204)
def delete_library(library_id: int, db: Session = Depends(get_db)):
    li = db.get(Library, library_id)
    if not li:
        return
    db.delete(li)

# --- Media scan & items endpoints ---
from lhmm.db.models import MediaFile, MediaItem, Series, LibraryScan
from lhmm.services.scanner import scan_library
import json as _json

@router.post("/{library_id}/scan")
def start_scan(library_id: int, bg: BackgroundTasks, db: Session = Depends(get_db)):
    if not db.get(Library, library_id):
        raise not_found()
    bg.add_task(scan_library, library_id)
    return {"queued": True}

@router.get("/{library_id}/items")
def list_items(library_id: int, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    if not db.get(Library, library_id):
        raise not_found()
    stmt = (
        select(MediaFile, MediaItem, Series)
        .join(MediaItem, MediaFile.item_id == MediaItem.id)
        .join(Library, MediaFile.library_id == Library.id)
        .outerjoin(Series, MediaItem.series_id == Series.id)
        .where(MediaFile.library_id == library_id)
        .order_by(MediaFile.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = db.execute(stmt).all()
    items = []
    for mf, mi, se in rows:
        items.append({
            "file_id": mf.id,
            "path": mf.rel_path,
            "size": mf.size,
            "kind": mi.kind,
            "title": mi.title,
            "year": mi.year,
            "series": se.name if se else None,
            "season": mi.season,
            "episode": mi.episode,
        })
    total = db.scalar(select(func.count()).select_from(MediaFile).where(MediaFile.library_id == library_id)) or 0
    return {"total": total, "items": items}

@router.get("/{library_id}/scans")
def list_scans(library_id: int, limit: int = 10, db: Session = Depends(get_db)):
    if not db.get(Library, library_id):
        raise not_found()
    stmt = (
        select(LibraryScan)
        .where(LibraryScan.library_id == library_id)
        .order_by(LibraryScan.id.desc())
        .limit(limit)
    )
    scans = [
        {
            "id": s.id,
            "status": s.status,
            "stats": (_json.loads(s.stats_json or "{}") if isinstance(s.stats_json, str) else s.stats_json) or {},
            "started_at": s.started_at,
            "finished_at": s.finished_at,
        }
        for s in db.execute(stmt).scalars().all()
    ]
    return {"items": scans}
