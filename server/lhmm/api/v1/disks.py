from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from lhmm.db.models import Disk, Library
from lhmm.api.deps import get_db
from lhmm.api.pagination import parse_pagination
from lhmm.api.errors import bad_request, not_found

router = APIRouter(prefix="/disks", tags=["disks"])


class DiskIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    mount_path: str = Field(min_length=1, max_length=512)


class DiskOut(BaseModel):
    id: int
    name: str
    mount_path: str

    class Config:
        from_attributes = True


@router.get("")
def list_disks(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    sort: str = Query("name"),
    db: Session = Depends(get_db),
):
    offset, limit = parse_pagination(page, per_page)
    order = Disk.name.asc() if sort == "name" else Disk.name.desc() if sort == "-name" else Disk.id.asc()
    total = db.scalar(select(func.count()).select_from(Disk)) or 0
    items = db.execute(select(Disk).order_by(order).offset(offset).limit(limit)).scalars().all()
    return {
        "total": total,
        "page": page,
        "per_page": limit,
        "items": [DiskOut.model_validate(i).model_dump() for i in items],
    }


@router.post("")
def create_disk(payload: DiskIn, db: Session = Depends(get_db)):
    if db.scalar(select(func.count()).select_from(Disk).where(Disk.name == payload.name)):
        raise bad_request("Disk name already exists")
    d = Disk(name=payload.name, mount_path=payload.mount_path)
    db.add(d)
    db.flush()
    return DiskOut.model_validate(d).model_dump()


@router.get("/{disk_id}")
def get_disk(disk_id: int, db: Session = Depends(get_db)):
    d = db.get(Disk, disk_id)
    if not d:
        raise not_found()
    return DiskOut.model_validate(d).model_dump()


@router.put("/{disk_id}")
def update_disk(disk_id: int, payload: DiskIn, db: Session = Depends(get_db)):
    d = db.get(Disk, disk_id)
    if not d:
        raise not_found()
    if payload.name != d.name and db.scalar(select(func.count()).select_from(Disk).where(Disk.name == payload.name)):
        raise bad_request("Disk name already exists")
    d.name = payload.name
    d.mount_path = payload.mount_path
    db.add(d)
    return DiskOut.model_validate(d).model_dump()


@router.delete("/{disk_id}", status_code=204)
def delete_disk(disk_id: int, db: Session = Depends(get_db)):
    d = db.get(Disk, disk_id)
    if not d:
        return
    if db.scalar(select(func.count()).select_from(Library).where(Library.root_disk_id == disk_id)):
        raise bad_request("Disk has libraries; move or delete libraries first")
    db.delete(d)
