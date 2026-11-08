from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


pattern_tags = Table(
    "pattern_tags",
    Base.metadata,
    Column("pattern_id", String(128), ForeignKey("patterns.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Pattern(Base):
    __tablename__ = "patterns"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    catalog: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    original_title: Mapped[str | None] = mapped_column(Text)
    motif_type: Mapped[str] = mapped_column(String(64), nullable=False, default="其他", index=True)
    secondary: Mapped[str | None] = mapped_column(String(128))
    dynasty: Mapped[str] = mapped_column(String(64), nullable=False, default="年代未定", index=True)
    date_text: Mapped[str | None] = mapped_column(Text)
    century: Mapped[str | None] = mapped_column(String(64))
    carrier: Mapped[str] = mapped_column(String(64), nullable=False, default="其他", index=True)
    description: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="其他", index=True)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    license: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="confirmed", index=True)
    annotator: Mapped[str | None] = mapped_column(String(64))
    notes: Mapped[str | None] = mapped_column(Text)
    dataset_origin: Mapped[str | None] = mapped_column(String(128))
    has_image: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    label_valid: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    colors_json: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    images: Mapped[list[PatternImage]] = relationship(
        back_populates="pattern",
        cascade="all, delete-orphan",
        order_by="PatternImage.sort_order",
    )
    tags: Mapped[list[Tag]] = relationship(
        secondary=pattern_tags,
        back_populates="patterns",
    )
    favorites: Mapped[list[Favorite]] = relationship(
        back_populates="pattern", cascade="all, delete-orphan"
    )
    browse_logs: Mapped[list[BrowseLog]] = relationship(
        back_populates="pattern", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("source", "source_id", name="uq_pattern_source_id"),
        Index("ix_pattern_filter", "motif_type", "dynasty", "carrier"),
    )


class PatternImage(Base):
    __tablename__ = "pattern_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pattern_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("patterns.id", ondelete="CASCADE"), index=True
    )
    relative_path: Mapped[str | None] = mapped_column(Text)
    external_url: Mapped[str | None] = mapped_column(Text)
    alt_text: Mapped[str | None] = mapped_column(String(512))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    pattern: Mapped[Pattern] = relationship(back_populates="images")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dimension: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str | None] = mapped_column(String(128))
    description: Mapped[str | None] = mapped_column(Text)

    patterns: Mapped[list[Pattern]] = relationship(
        secondary=pattern_tags,
        back_populates="tags",
    )

    __table_args__ = (
        UniqueConstraint("dimension", "name", name="uq_tag_dimension_name"),
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    favorites: Mapped[list[Favorite]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    browse_logs: Mapped[list[BrowseLog]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Favorite(Base):
    __tablename__ = "favorites"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    pattern_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("patterns.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped[User] = relationship(back_populates="favorites")
    pattern: Mapped[Pattern] = relationship(back_populates="favorites")


class BrowseLog(Base):
    __tablename__ = "browse_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    pattern_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("patterns.id", ondelete="CASCADE"), index=True
    )
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )
    referer: Mapped[str | None] = mapped_column(String(512))

    user: Mapped[User] = relationship(back_populates="browse_logs")
    pattern: Mapped[Pattern] = relationship(back_populates="browse_logs")

