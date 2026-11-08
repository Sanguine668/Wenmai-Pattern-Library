from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image, ImageOps
from sqlalchemy import case, func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from .config import API_TITLE, API_VERSION, DEMO_USERNAME, PROJECT_ROOT
from .database import Base, SessionLocal, engine, get_db
from .deps import get_current_user, get_optional_user, require_admin
from .importer import ensure_admin_user, ensure_demo_user, import_master_data
from .models import BrowseLog, Favorite, Pattern, PatternImage, Tag, User
from .ratelimit import (
    clear_failures,
    login_key,
    record_failure,
    remaining_lock_seconds,
)
from .schemas import (
    LoginRequest,
    PatternPatch,
    PatternWrite,
    RegisterRequest,
    UserCreate,
    UserPatch,
)
from .security import (
    BEARER_CHALLENGE,
    create_access_token,
    hash_password,
    password_needs_rehash,
    verify_password,
)
from .serializers import serialize_pattern, serialize_user


def ensure_browse_log_unique_index() -> None:
    """SQLite 下为浏览记录补 (user_id, pattern_id) 唯一索引，顺带清理历史重复。"""
    if engine.url.get_backend_name() != "sqlite":
        return
    with engine.begin() as connection:
        connection.execute(
            text(
                "DELETE FROM browse_logs WHERE id NOT IN "
                "(SELECT MAX(id) FROM browse_logs GROUP BY user_id, pattern_id)"
            )
        )
        connection.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_browse_logs_user_pattern "
                "ON browse_logs (user_id, pattern_id)"
            )
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    ensure_browse_log_unique_index()
    with SessionLocal() as db:
        ensure_demo_user(db)
        ensure_admin_user(db)
        count = db.scalar(select(func.count()).select_from(Pattern)) or 0
        if count == 0:
            import_master_data(db, reset=False, extract_colors=True)
    yield


app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description="中华传统纹样资源、图片、标签、用户与浏览收藏记录的增删改查接口。",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_pattern_or_404(db: Session, pattern_id: str) -> Pattern:
    pattern = db.scalar(
        select(Pattern)
        .where(Pattern.id == pattern_id)
        .options(
            selectinload(Pattern.images),
            selectinload(Pattern.tags),
        )
    )
    if pattern is None:
        raise HTTPException(status_code=404, detail="纹样记录不存在")
    return pattern


def get_user_or_404(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user


def sync_pattern_tags(db: Session, pattern: Pattern) -> None:
    names = [
        ("motif", pattern.motif_type),
        ("secondary", pattern.secondary),
        ("dynasty", pattern.dynasty),
        ("carrier", pattern.carrier),
        ("status", pattern.status),
    ]
    tags = []
    for dimension, name in names:
        name = (name or "").strip()
        if not name:
            continue
        tag = db.scalar(select(Tag).where(Tag.dimension == dimension, Tag.name == name))
        if tag is None:
            tag = Tag(dimension=dimension, name=name)
            db.add(tag)
            db.flush()
        tags.append(tag)
    pattern.tags = tags


@app.get("/api/health")
def health(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(Pattern)) or 0
    return {
        "status": "ok",
        "database": engine.url.get_backend_name(),
        "patterns": total,
    }


@app.post("/api/auth/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(status_code=409, detail="用户名已存在")
    if payload.email and db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="邮箱已被使用")
    user = User(
        username=payload.username,
        display_name=payload.display_name,
        email=payload.email or None,
        password_hash=hash_password(payload.password),
        is_admin=False,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"token": create_access_token(user), "user": serialize_user(user)}


@app.post("/api/auth/login")
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    limiter_key = login_key(
        payload.username, request.client.host if request.client else None
    )
    retry_after = remaining_lock_seconds(limiter_key)
    if retry_after:
        raise HTTPException(
            status_code=429,
            detail="登录尝试过于频繁，请稍后再试",
            headers={"Retry-After": str(retry_after)},
        )
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.password_hash):
        record_failure(limiter_key)
        raise HTTPException(
            status_code=401,
            detail="用户名或密码不正确",
            headers=BEARER_CHALLENGE,
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账号已停用，请联系管理员")
    clear_failures(limiter_key)
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(payload.password)
        db.commit()
    return {"token": create_access_token(user), "user": serialize_user(user)}


@app.get("/api/auth/me")
def current_profile(user: User = Depends(get_current_user)):
    return serialize_user(user)


@app.get("/api/stats")
def stats(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(Pattern)) or 0
    with_images = (
        db.scalar(select(func.count()).where(Pattern.has_image.is_(True))) or 0
    )
    trainable = (
        db.scalar(
            select(func.count()).where(
                Pattern.has_image.is_(True),
                Pattern.status == "confirmed",
                Pattern.label_valid.is_(True),
            )
        )
        or 0
    )
    discarded = (
        db.scalar(select(func.count()).where(Pattern.status == "discarded")) or 0
    )
    no_image = db.scalar(select(func.count()).where(Pattern.has_image.is_(False))) or 0
    return {
        "total": total,
        "withImages": with_images,
        "trainable": trainable,
        "discarded": discarded,
        "noImage": no_image,
    }


def pattern_conditions(
    *,
    keyword: str = "",
    motif: str = "",
    dynasty: str = "",
    carrier: str = "",
    source: str = "",
    status: str = "",
    has_image: bool | None = None,
    exclude: set[str] | None = None,
):
    skip = exclude or set()
    conditions = []
    if keyword.strip() and "keyword" not in skip:
        like = f"%{keyword.strip()}%"
        conditions.append(
            or_(
                Pattern.name.like(like),
                Pattern.original_title.like(like),
                Pattern.description.like(like),
                Pattern.source_id.like(like),
                Pattern.motif_type.like(like),
                Pattern.carrier.like(like),
                Pattern.secondary.like(like),
            )
        )
    if motif and "motif" not in skip:
        conditions.append(Pattern.motif_type == motif)
    if dynasty and "dynasty" not in skip:
        conditions.append(Pattern.dynasty == dynasty)
    if carrier and "carrier" not in skip:
        conditions.append(Pattern.carrier == carrier)
    if source and "source" not in skip:
        conditions.append(Pattern.source == source)
    if status and "status" not in skip:
        conditions.append(Pattern.status == status)
    if has_image is not None and "has_image" not in skip:
        conditions.append(Pattern.has_image.is_(has_image))
    return conditions


@app.get("/api/meta")
def meta(db: Session = Depends(get_db)):
    def grouped(column):
        rows = db.execute(
            select(column, func.count())
            .group_by(column)
            .order_by(func.count().desc(), column)
        ).all()
        return [
            {"label": value or "其他", "count": count}
            for value, count in rows
            if value
        ]

    def source_grouped():
        rows = db.execute(
            select(Pattern.source, func.count())
            .group_by(Pattern.source)
            .order_by(func.count().desc())
        ).all()
        labels = {
            "met": "大都会艺术博物馆",
            "cleveland": "克利夫兰艺术博物馆",
            "commons": "Wikimedia Commons",
            "artic": "芝加哥艺术博物馆",
            "dunhuang": "数字敦煌",
        }
        return [
            {"value": value, "label": labels.get(value, value), "count": count}
            for value, count in rows
        ]

    return {
        "motifs": grouped(Pattern.motif_type),
        "dynasties": grouped(Pattern.dynasty),
        "carriers": grouped(Pattern.carrier),
        "statuses": grouped(Pattern.status),
        "sources": source_grouped(),
    }


def facet_counts(db: Session, column, key: str, **filters) -> list[dict]:
    """某个维度的计数：应用除该维度外的所有筛选条件。"""
    conditions = pattern_conditions(exclude={key}, **filters)
    rows = db.execute(
        select(column, func.count()).where(*conditions).group_by(column)
    ).all()
    counts = {value: count for value, count in rows if value}
    global_rows = db.execute(
        select(column, func.count())
        .group_by(column)
        .order_by(func.count().desc(), column)
    ).all()
    return [
        {"label": value, "count": counts.get(value, 0)}
        for value, _ in global_rows
        if value
    ]


@app.get("/api/facets")
def facets(
    keyword: str = "",
    motif: str = "",
    dynasty: str = "",
    carrier: str = "",
    source: str = "",
    status: str = "",
    has_image: bool | None = None,
    db: Session = Depends(get_db),
):
    filters = {
        "keyword": keyword,
        "motif": motif,
        "dynasty": dynasty,
        "carrier": carrier,
        "source": source,
        "status": status,
        "has_image": has_image,
    }
    total = (
        db.scalar(
            select(func.count())
            .select_from(Pattern)
            .where(*pattern_conditions(**filters))
        )
        or 0
    )
    return {
        "motifs": facet_counts(db, Pattern.motif_type, "motif", **filters),
        "dynasties": facet_counts(db, Pattern.dynasty, "dynasty", **filters),
        "carriers": facet_counts(db, Pattern.carrier, "carrier", **filters),
        "total": total,
    }


@app.get("/api/patterns")
def list_patterns(
    keyword: str = "",
    motif: str = "",
    dynasty: str = "",
    carrier: str = "",
    source: str = "",
    status: str = "",
    has_image: bool | None = None,
    sort: str = "curated",
    limit: int = Query(default=24, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    conditions = pattern_conditions(
        keyword=keyword,
        motif=motif,
        dynasty=dynasty,
        carrier=carrier,
        source=source,
        status=status,
        has_image=has_image,
    )

    total = db.scalar(select(func.count()).select_from(Pattern).where(*conditions)) or 0
    order = []
    if sort == "title":
        order.append(Pattern.name.asc())
    elif sort == "dynasty":
        order.extend([Pattern.dynasty.asc(), Pattern.name.asc()])
    elif sort == "latest":
        order.append(Pattern.updated_at.desc())
    else:
        order.extend(
            [
                case((Pattern.has_image.is_(True), 0), else_=1),
                Pattern.source.asc(),
                Pattern.source_id.asc(),
            ]
        )
    rows = db.scalars(
        select(Pattern)
        .where(*conditions)
        .options(selectinload(Pattern.images), selectinload(Pattern.tags))
        .order_by(*order)
        .offset(offset)
        .limit(limit)
    ).all()
    return {
        "items": [serialize_pattern(item) for item in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@app.get("/api/patterns/{pattern_id}")
def get_pattern(pattern_id: str, db: Session = Depends(get_db)):
    pattern = get_pattern_or_404(db, pattern_id)
    related_rows = db.scalars(
        select(Pattern)
        .where(
            Pattern.id != pattern.id,
            Pattern.has_image.is_(True),
            or_(
                Pattern.motif_type == pattern.motif_type,
                Pattern.dynasty == pattern.dynasty,
                Pattern.carrier == pattern.carrier,
            ),
        )
        .options(selectinload(Pattern.images), selectinload(Pattern.tags))
        .limit(4)
    ).all()
    return serialize_pattern(
        pattern,
        related=[serialize_pattern(item) for item in related_rows],
    )


@app.post("/api/patterns", status_code=201)
def create_pattern(
    payload: PatternWrite,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    source = payload.source or "manual"
    source_id = payload.source_id or uuid4().hex
    pattern_id = f"{source}-{source_id}"
    if db.get(Pattern, pattern_id) is not None:
        raise HTTPException(status_code=409, detail="该来源编号已存在")
    values = payload.model_dump(exclude={"image_url"})
    values["source_id"] = source_id
    pattern = Pattern(
        id=pattern_id,
        catalog=f"{source.upper()}-{source_id}",
        **values,
    )
    db.add(pattern)
    db.flush()
    if payload.image_url:
        db.add(
            PatternImage(
                pattern_id=pattern.id,
                external_url=payload.image_url,
                alt_text=pattern.name,
                is_primary=True,
                sort_order=0,
            )
        )
        pattern.has_image = True
    sync_pattern_tags(db, pattern)
    db.commit()
    return serialize_pattern(get_pattern_or_404(db, pattern.id))


@app.patch("/api/patterns/{pattern_id}")
def update_pattern(
    pattern_id: str,
    payload: PatternPatch,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    pattern = get_pattern_or_404(db, pattern_id)
    values = payload.model_dump(exclude_unset=True, exclude={"image_url"})
    for key, value in values.items():
        setattr(pattern, key, value)
    if payload.image_url is not None:
        primary = next((item for item in pattern.images if item.is_primary), None)
        if primary is None:
            primary = PatternImage(
                pattern_id=pattern.id,
                alt_text=pattern.name,
                is_primary=True,
                sort_order=0,
            )
            db.add(primary)
        primary.external_url = payload.image_url or None
        pattern.has_image = bool(payload.image_url) or any(
            item.relative_path for item in pattern.images
        )
    sync_pattern_tags(db, pattern)
    db.commit()
    return serialize_pattern(get_pattern_or_404(db, pattern.id))


@app.delete("/api/patterns/{pattern_id}", status_code=204)
def delete_pattern(
    pattern_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    pattern = get_pattern_or_404(db, pattern_id)
    db.delete(pattern)
    db.commit()


@app.get("/api/images/{image_id}")
def serve_image(image_id: int, db: Session = Depends(get_db)):
    image = db.get(PatternImage, image_id)
    if image is None or not image.relative_path:
        raise HTTPException(status_code=404, detail="图片不存在")
    path = (PROJECT_ROOT / image.relative_path).resolve()
    if not path.is_relative_to(PROJECT_ROOT) or not path.is_file():
        raise HTTPException(status_code=404, detail="图片文件不存在")
    if path.suffix.lower() in {".tif", ".tiff"}:
        cache_dir = PROJECT_ROOT / "data" / "image_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / f"{image.id}-{path.stat().st_mtime_ns}.jpg"
        if not cache_path.is_file():
            try:
                with Image.open(path) as source:
                    frame = ImageOps.exif_transpose(source)
                    frame.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
                    if frame.mode in ("RGBA", "LA") or (
                        frame.mode == "P" and "transparency" in frame.info
                    ):
                        rgba = frame.convert("RGBA")
                        background = Image.new("RGB", rgba.size, (245, 244, 239))
                        background.paste(rgba, mask=rgba.getchannel("A"))
                        frame = background
                    else:
                        frame = frame.convert("RGB")
                    temp_path = cache_dir / f".{uuid4().hex}.tmp"
                    frame.save(temp_path, "JPEG", quality=88, optimize=True)
                    temp_path.replace(cache_path)
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(status_code=500, detail="图片转换失败") from exc
        return FileResponse(
            cache_path,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=86400"},
            filename=cache_path.name,
        )
    return FileResponse(
        path,
        headers={"Cache-Control": "public, max-age=86400"},
        filename=path.name,
    )


@app.get("/api/tags")
def list_tags(db: Session = Depends(get_db)):
    rows = db.execute(
        select(Tag.dimension, Tag.name, func.count())
        .join(Tag.patterns)
        .group_by(Tag.id, Tag.dimension, Tag.name)
        .order_by(Tag.dimension, func.count().desc())
    ).all()
    return [
        {"dimension": dimension, "name": name, "count": count}
        for dimension, name, count in rows
    ]


@app.get("/api/users")
def list_users(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return [serialize_user(item) for item in db.scalars(select(User).order_by(User.id)).all()]


@app.post("/api/users", status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if db.scalar(select(User).where(User.username == payload.username)):
        raise HTTPException(status_code=409, detail="用户名已存在")
    if payload.email and db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="邮箱已被使用")
    user = User(
        username=payload.username,
        display_name=payload.display_name,
        email=payload.email or None,
        password_hash=hash_password(payload.password),
        is_admin=payload.is_admin,
        is_active=payload.is_active,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@app.get("/api/users/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    user = get_user_or_404(db, user_id)
    if current.id != user.id and not current.is_admin:
        raise HTTPException(status_code=403, detail="无权查看其他用户")
    return serialize_user(user)


def assert_self_or_admin(current: User, user: User) -> None:
    if current.id != user.id and not current.is_admin:
        raise HTTPException(status_code=403, detail="无权操作其他用户")


@app.patch("/api/users/{user_id}")
def update_user(
    user_id: int,
    payload: UserPatch,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    user = get_user_or_404(db, user_id)
    assert_self_or_admin(current, user)
    values = payload.model_dump(exclude_unset=True, exclude={"password"})
    if "email" in values:
        values["email"] = values["email"] or None
        if values["email"] and db.scalar(
            select(User).where(
                User.email == values["email"], User.id != user.id
            )
        ):
            raise HTTPException(status_code=409, detail="邮箱已被使用")
    privileged = {"is_admin", "is_active"} & set(values)
    if user.username == DEMO_USERNAME and (privileged or payload.password is not None):
        raise HTTPException(
            status_code=400, detail="游客兜底账号的权限与密码不能修改"
        )
    if privileged:
        if not current.is_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以修改账号权限")
        if user.id == current.id:
            if values.get("is_admin") is False:
                raise HTTPException(status_code=400, detail="不能取消自己的管理员身份")
            if values.get("is_active") is False:
                raise HTTPException(status_code=400, detail="不能停用当前登录账号")
    for key, value in values.items():
        setattr(user, key, value)
    if payload.password is not None:
        user.password_hash = hash_password(payload.password)
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@app.delete("/api/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(require_admin),
):
    user = get_user_or_404(db, user_id)
    if user.id == current.id:
        raise HTTPException(status_code=400, detail="不能删除当前登录账号")
    if user.username == DEMO_USERNAME:
        raise HTTPException(status_code=400, detail="演示用户不能删除")
    db.delete(user)
    db.commit()


def get_demo_user(db: Session) -> User:
    user = db.scalar(select(User).where(User.username == DEMO_USERNAME))
    if user is None or not user.is_active:
        raise HTTPException(status_code=503, detail="游客账号尚未就绪")
    return user


def resolve_actor(db: Session, user: User | None) -> User:
    """登录用户操作自己的数据；未登录时回落到 demo 游客账号。"""
    return user if user is not None else get_demo_user(db)


def favorites_payload(db: Session, user_id: int) -> dict:
    rows = db.scalars(
        select(Pattern)
        .join(Favorite, Favorite.pattern_id == Pattern.id)
        .where(Favorite.user_id == user_id)
        .options(selectinload(Pattern.images), selectinload(Pattern.tags))
        .order_by(Favorite.created_at.desc())
    ).all()
    return {"items": [serialize_pattern(item) for item in rows]}


def add_favorite_row(db: Session, user_id: int, pattern_id: str) -> dict:
    get_pattern_or_404(db, pattern_id)
    favorite = db.get(Favorite, (user_id, pattern_id))
    if favorite is None:
        db.add(Favorite(user_id=user_id, pattern_id=pattern_id))
        try:
            db.commit()
        except IntegrityError:
            # 并发重复收藏时主键冲突，回滚即视为已收藏。
            db.rollback()
    return {"favorited": True}


def remove_favorite_row(db: Session, user_id: int, pattern_id: str) -> None:
    favorite = db.get(Favorite, (user_id, pattern_id))
    if favorite is not None:
        db.delete(favorite)
        db.commit()


def record_view_row(db: Session, user_id: int, pattern_id: str, referer: str | None) -> dict:
    get_pattern_or_404(db, pattern_id)
    recent = db.scalar(
        select(BrowseLog).where(
            BrowseLog.user_id == user_id,
            BrowseLog.pattern_id == pattern_id,
        )
    )
    viewed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if recent is None:
        db.add(
            BrowseLog(
                user_id=user_id,
                pattern_id=pattern_id,
                referer=referer,
                viewed_at=viewed_at,
            )
        )
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            recent = db.scalar(
                select(BrowseLog).where(
                    BrowseLog.user_id == user_id,
                    BrowseLog.pattern_id == pattern_id,
                )
            )
            if recent is not None:
                recent.viewed_at = viewed_at
                recent.referer = referer
                db.commit()
    else:
        recent.viewed_at = viewed_at
        recent.referer = referer
        db.commit()
    return {"recorded": True}


def history_payload(db: Session, user_id: int, limit: int) -> dict:
    rows = db.execute(
        select(Pattern, BrowseLog.viewed_at)
        .join(BrowseLog, BrowseLog.pattern_id == Pattern.id)
        .where(BrowseLog.user_id == user_id)
        .options(selectinload(Pattern.images), selectinload(Pattern.tags))
        .order_by(BrowseLog.viewed_at.desc(), BrowseLog.id.desc())
        .limit(limit)
    ).all()
    return {
        "items": [
            {**serialize_pattern(pattern), "viewedAt": viewed_at.isoformat()}
            for pattern, viewed_at in rows
        ]
    }


@app.get("/api/me/favorites")
def list_my_favorites(
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    actor = resolve_actor(db, user)
    return favorites_payload(db, actor.id)


@app.post("/api/me/favorites/{pattern_id}", status_code=201)
def add_my_favorite(
    pattern_id: str,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    actor = resolve_actor(db, user)
    return add_favorite_row(db, actor.id, pattern_id)


@app.delete("/api/me/favorites/{pattern_id}", status_code=204)
def remove_my_favorite(
    pattern_id: str,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    actor = resolve_actor(db, user)
    remove_favorite_row(db, actor.id, pattern_id)


@app.get("/api/me/history")
def my_history(
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    actor = resolve_actor(db, user)
    return history_payload(db, actor.id, limit)


@app.post("/api/me/views/{pattern_id}", status_code=201)
def record_my_view(
    pattern_id: str,
    request: Request,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    actor = resolve_actor(db, user)
    return record_view_row(db, actor.id, pattern_id, request.headers.get("referer"))


@app.get("/api/users/{user_id}/favorites")
def list_favorites(
    user_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    user = get_user_or_404(db, user_id)
    assert_self_or_admin(current, user)
    return favorites_payload(db, user_id)


@app.post("/api/users/{user_id}/favorites/{pattern_id}", status_code=201)
def add_favorite(
    user_id: int,
    pattern_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    user = get_user_or_404(db, user_id)
    assert_self_or_admin(current, user)
    return add_favorite_row(db, user_id, pattern_id)


@app.delete("/api/users/{user_id}/favorites/{pattern_id}", status_code=204)
def remove_favorite(
    user_id: int,
    pattern_id: str,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    user = get_user_or_404(db, user_id)
    assert_self_or_admin(current, user)
    remove_favorite_row(db, user_id, pattern_id)


@app.post("/api/users/{user_id}/views/{pattern_id}", status_code=201)
def record_view(
    user_id: int,
    pattern_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    user = get_user_or_404(db, user_id)
    assert_self_or_admin(current, user)
    return record_view_row(db, user_id, pattern_id, request.headers.get("referer"))


@app.get("/api/users/{user_id}/history")
def browse_history(
    user_id: int,
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    user = get_user_or_404(db, user_id)
    assert_self_or_admin(current, user)
    return history_payload(db, user_id, limit)

