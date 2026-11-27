"""Content recommendation using decayed favorites, views and recent popularity."""
from collections import Counter
from datetime import datetime, timedelta, timezone
from math import sqrt

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from .config import DEMO_USERNAME
from .models import BrowseLog, Favorite, Pattern, User
from .serializers import serialize_pattern

DIMENSIONS = {"motif_type": 0.5, "dynasty": 0.2, "carrier": 0.3}
UNKNOWN = {"", "其他", "其他（未归类）", "未知", "年代未定", "年代未知"}


def recommend(db: Session, user: User, limit: int) -> dict:
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=30)).replace(tzinfo=None)
    patterns = db.scalars(select(Pattern).where(
        Pattern.has_image.is_(True), Pattern.status != "discarded",
        Pattern.images.any(),
    ).options(selectinload(Pattern.images), selectinload(Pattern.tags))).all()
    available = {pattern.id: pattern for pattern in patterns}
    favorites = db.execute(select(Favorite.pattern_id, Favorite.created_at).where(
        Favorite.user_id == user.id,
    )).all()
    views = db.execute(select(BrowseLog.pattern_id, func.max(BrowseLog.viewed_at)).where(
        BrowseLog.user_id == user.id,
    ).group_by(BrowseLog.pattern_id)).all()
    interests = {dimension: Counter() for dimension in DIMENSIONS}
    interacted = set()
    # Each effective favorite and most recent view contributes once.
    for records, strength in ((favorites, 3), (views, 1)):
        for pattern_id, occurred_at in records:
            pattern = available.get(pattern_id)
            if pattern is None or user.username == DEMO_USERNAME:
                continue
            occurred_at = occurred_at or now
            age = max(0, (now - occurred_at.replace(tzinfo=timezone.utc)).total_seconds() / 86400)
            weight = strength * 2 ** (-age / 30)
            interacted.add(pattern_id)
            for dimension in DIMENSIONS:
                value = getattr(pattern, dimension) or ""
                if value not in UNKNOWN:
                    interests[dimension][value] += weight
    norms = {dimension: sqrt(sum(value ** 2 for value in counts.values()))
             for dimension, counts in interests.items()}
    popularity = dict(db.execute(select(
        Favorite.pattern_id, func.count(func.distinct(Favorite.user_id)),
    ).join(User).where(
        Favorite.created_at >= cutoff, User.username != DEMO_USERNAME,
        User.is_active.is_(True),
    ).group_by(Favorite.pattern_id)).all())
    favorite_ids = {row[0] for row in favorites}
    candidates = [pattern for pattern in patterns if pattern.id not in favorite_ids]
    max_popularity = max((popularity.get(pattern.id, 0) for pattern in candidates), default=0)
    blend = 0.8 * min(len(interacted) / 10, 1)
    ranked = []
    for pattern in candidates:
        matches = []
        total = 0
        for dimension, importance in DIMENSIONS.items():
            value = getattr(pattern, dimension) or ""
            if norms[dimension] and value not in UNKNOWN:
                similarity = interests[dimension][value] / norms[dimension]
                total += importance * similarity
                matches.append((importance * similarity, value))
        content = total
        popular = popularity.get(pattern.id, 0) / max_popularity if max_popularity else 0
        score = blend * content + (1 - blend) * popular
        strongest = max(matches, default=(0, ""))
        reason = "馆藏精选"
        if blend * content > 0 and blend * content >= (1 - blend) * popular:
            reason = f"根据你收藏和浏览的{strongest[1]}推荐"
        elif popular:
            reason = "近期读者收藏推荐"
        ranked.append((score, pattern, content, popular, reason))
    ranked.sort(key=lambda row: (-row[0], row[1].id))
    selected, deferred = [], []
    counts = Counter()
    for row in ranked:
        motif = row[1].motif_type
        if counts[motif] < 3:
            selected.append(row)
            counts[motif] += 1
        else:
            deferred.append(row)
    selected = (selected[:limit] + deferred)[:limit]
    items = []
    for score, pattern, content, popular, reason in selected:
        payload = serialize_pattern(pattern)
        payload.update(reason=reason, score=round(score, 6),
                       contentScore=round(content, 6), popularityScore=round(popular, 6))
        items.append(payload)
    return {"items": items, "personalizationWeight": round(blend, 6), "interactionCount": len(interacted)}
