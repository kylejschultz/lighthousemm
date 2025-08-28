from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy import String, Integer, BigInteger, ForeignKey, UniqueConstraint, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from lhmm.db.base import Base

def now_ts() -> int:
    return int(datetime.now(timezone.utc).timestamp())

class Disk(Base):
    __tablename__ = "disks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    mount_path: Mapped[str] = mapped_column(String(512), nullable=False)

class Library(Base):
    __tablename__ = "libraries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(16), nullable=False)  # 'movie' | 'tv'
    root_disk_id: Mapped[int] = mapped_column(ForeignKey("disks.id", ondelete="RESTRICT"), nullable=False)
    root_subdir: Mapped[str] = mapped_column(String(256), nullable=False)  # e.g., Movies, TV, Anime
    settings_json: Mapped[str] = mapped_column(String, nullable=False, default="{}")
    disk: Mapped["Disk"] = relationship(backref="libraries")

    __table_args__ = (Index("ix_libraries_type", "type"),)

class Series(Base):
    __tablename__ = "series"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tmdb_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)

class MediaItem(Base):
    __tablename__ = "media_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 'movie' | 'episode'
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    tmdb_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    overview: Mapped[str | None] = mapped_column(String, nullable=True)
    poster_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    backdrop_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    series_id: Mapped[int | None] = mapped_column(ForeignKey("series.id", ondelete="SET NULL"), nullable=True)
    season: Mapped[int | None] = mapped_column(Integer, nullable=True)
    episode: Mapped[int | None] = mapped_column(Integer, nullable=True)
    added_at: Mapped[int] = mapped_column(BigInteger, default=now_ts, nullable=False)

    series: Mapped[Series | None] = relationship(backref="items")

    __table_args__ = (
        # Allow multiple episodes per tmdb series id; ensure uniqueness across dimensions
        UniqueConstraint("kind", "tmdb_id", "series_id", "season", "episode", name="uq_mediaitem_unique"),
        Index("ix_mediaitem_tmdb", "tmdb_id"),
        Index("ix_mediaitem_title", "title"),
        Index("ix_mediaitem_series_se", "series_id", "season", "episode"),
    )

class MediaFile(Base):
    __tablename__ = "media_files"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False)
    library_id: Mapped[int] = mapped_column(ForeignKey("libraries.id", ondelete="CASCADE"), nullable=False)
    rel_path: Mapped[str] = mapped_column(String(1024), nullable=False)  # path relative to library root
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mtime: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    quality_json: Mapped[str] = mapped_column(String, nullable=False, default="{}")
    created_at: Mapped[int] = mapped_column(BigInteger, default=now_ts, nullable=False)

    item: Mapped["MediaItem"] = relationship(backref="files")
    library: Mapped["Library"] = relationship(backref="files")

    __table_args__ = (
        UniqueConstraint("library_id", "rel_path", name="uq_file_unique_per_library"),
        Index("ix_mediafile_item", "item_id"),
    )

class LibraryScan(Base):
    __tablename__ = "library_scans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    library_id: Mapped[int] = mapped_column(ForeignKey("libraries.id", ondelete="CASCADE"), nullable=False)
    started_at: Mapped[int] = mapped_column(BigInteger, default=now_ts, nullable=False)
    finished_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")  # queued|running|succeeded|failed
    stats_json: Mapped[str] = mapped_column(String, nullable=False, default="{}")

class Indexer(Base):
    __tablename__ = "indexers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    url: Mapped[str] = mapped_column(String(512), nullable=False)
    api_key: Mapped[str | None] = mapped_column(String(256), nullable=True)
    capabilities_json: Mapped[str] = mapped_column(String, nullable=False, default="{}")

class Job(Base):
    __tablename__ = "jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")  # queued|running|done|error
    payload_json: Mapped[str] = mapped_column(String, nullable=False, default="{}")
    started_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    finished_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

class AppConfig(Base):
    __tablename__ = "app_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    data: Mapped[dict] = mapped_column(JSON, default=dict)
