# Leaderboard & Hall of Fame — Implementation Plan

> [!CAUTION]
> **For the executing model:** Read this plan top to bottom before writing a single line of code.
> Follow phases in strict order. Do not skip steps. Do not invent patterns not shown here.
> After completing each phase, run the verification-loop skill before proceeding.

---

## Branch Strategy

This work is split across two sequential branches. The UI branch is created **from** the backend
branch, not from `main`.

| Branch | Phases | Merges into |
|---|---|---|
| `feature/leaderboard-backend` | 1 – 10 | `main` (after review) |
| `feature/leaderboard-ui` | 11 – 12 | `feature/leaderboard-backend` (before that branch merges) |

```bash
# Executing model starts on:
git checkout -b feature/leaderboard-backend

# After phases 1-10 are complete and committed, the UI branch is created:
git checkout -b feature/leaderboard-ui
```

> [!NOTE]
> Phase 1 (the `sold_at` bug fix) must be committed first, independently, with the commit
> message: `fix: add sold_at timestamp to Item — leaderboard transaction anchor`

---

## Overview

This plan implements a full leaderboard system for Reuni, including live weekly and seasonal
rankings, frozen historical Hall of Fame snapshots, automated scheduler resets, GDPR-safe
account deletion handling, and a university-config-driven single source of truth.

> [!IMPORTANT]
> This plan was produced after an exhaustive design review. Follow every step in order.
> Do not deviate from the patterns described — they were chosen to satisfy specific GDPR,
> security (CSP, IDOR), and data-integrity constraints already established in the codebase.

---

## Design Decisions (Do Not Change)

| Decision | Value |
|---|---|
| Scoring attribution | Seller only (`Item.seller_id`) |
| Completed transaction anchor | `Item.sold_at` (new column) |
| Week boundary | Monday 00:00 → Sunday 23:59 `Europe/London` timezone |
| Live leaderboard source | Aggregate from `items` table. **Never** use `User.kg_saved_total` |
| Snapshot storage | Self-contained frozen rows (name, kg, rank copied at archive time) |
| Leaderboard visibility | `@login_required` + `@verified_required` |
| Caching | Flask-Caching `SimpleCache`, 5-minute TTL |
| Scheduler timezone | `Europe/London` on all cron jobs |
| Snapshot idempotency | Check if snapshot for period+domain already exists before archiving |
| Cross-university comparison | Live computed query only — no stored cross-uni snapshot table |
| Who appears on leaderboard | `User.role == 'student'`, `User.is_active == True`, `User.show_on_leaderboard == True`, `≥ 1 transaction in period` |
| Tiebreakers | `SUM(kg_saved) DESC` → `COUNT(item_id) DESC` → `MIN(sold_at) ASC` |
| Hall of Fame count | Top 3 per period (Weekly HoF), Top 3 per season (Seasonal HoF) |
| Weekly HoF history | Last 4 completed weeks shown |
| Snapshot archive count | Top 10 per period archived |
| Eco-title pool | 10 curated titles assigned deterministically by rank position |
| Opt-out scope | Prospective only. Historical snapshots retain the name until account deletion |
| Empty leaderboard state | Show "no trades yet" message — do not show zero-kg entries |
| Email templates | New winner emails use `app/templates/emails/` Jinja2 templates. Existing emails are out of scope for this feature |

---

## Correct Import Paths (use exactly these — do not guess)

```python
# Decorators
from app.utils.decorators import verified_required, admin_required

# Cache (defined in app/__init__.py, import from app)
from app import db, cache, limiter

# Flask request context
from flask import Blueprint, render_template, redirect, url_for, flash, g, request, current_app
from flask_login import login_required, current_user

# Models (import only what you need per file)
from app.models import (
    User, Item, Season, WeeklySnapshot, SeasonalSnapshot,
    UniversityConfig, ECO_TITLES
)
```

## Eco-Title Pool (hardcoded constant)

```python
ECO_TITLES = [
    "Zero Waste Hero", "Carbon Crusher", "Green Champion", "Eco Warrior",
    "Circular Pioneer", "Planet Protector", "Waste Buster",
    "Sustainability Star", "Reuse Legend", "Eco Guardian",
]
# Usage: ECO_TITLES[rank - 1]  → e.g. rank=1 → "Zero Waste Hero #1"
# If rank > 10 (extremely rare tie edge case): f"Eco Hero #{rank}"
```

---

## Proposed Changes

---

### Phase 1 — Bug Fix (Do First)

#### [MODIFY] `app/routes/items.py` — `confirm_pin()` function

**Problem:** Line 645 clears `item.claimed_at = None` immediately after setting `item.is_sold = True`,
leaving no permanent timestamp for when the transaction was completed. The leaderboard needs this.

**Fix:** Add `item.sold_at` before clearing `claimed_at`.

Find the block starting at "# PIN is correct — complete the transaction" and change it to:

```python
# PIN is correct — complete the transaction
try:
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    item.is_sold = True
    item.sold_at = now_utc          # ← NEW: permanent completion timestamp
    seller = item.seller
    seller.kg_saved_total += item.kg_saved

    # Clear PIN fields (claimed_at tracks active claim state — clear it after sale)
    item.pin_code = None
    item.pin_expires_at = None
    item.claimed_at = None
    item.pin_attempts = 0

    db.session.commit()
    session.pop(f"pin_{item.id}", None)
```

#### [MODIFY] `app/routes/partner.py` — recent items query

Find line ~176:
```python
recent_items = query_recent.order_by(Item.claimed_at.desc()).limit(5).all()
```
Change to:
```python
recent_items = query_recent.order_by(Item.sold_at.desc()).limit(5).all()
```

---

### Phase 2 — New & Modified Database Models

#### [MODIFY] `app/models.py`

**Step 1 — Add `ECO_TITLES` constant** at the top of the file, after `CATEGORY_WEIGHTS`:

```python
ECO_TITLES = [
    "Zero Waste Hero", "Carbon Crusher", "Green Champion", "Eco Warrior",
    "Circular Pioneer", "Planet Protector", "Waste Buster",
    "Sustainability Star", "Reuse Legend", "Eco Guardian",
]
```

**Step 2 — Replace the `UniversityLogo` model** entirely with `UniversityConfig`:

```python
# ──────────────────────────────────────────────
# University Configuration Model
# (Replaces UniversityLogo — single source of truth for all university data)
# ──────────────────────────────────────────────
class UniversityConfig(db.Model):
    __tablename__ = "university_configs"

    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(100), unique=True, nullable=False, index=True)
    subdomain_slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(200), nullable=False)
    email_domain = db.Column(db.String(100), nullable=False)  # e.g. "brookes.ac.uk"
    timezone = db.Column(db.String(50), nullable=False, default="Europe/London")
    brand_color = db.Column(db.String(7), nullable=False, default="#1a1a2e")
    brand_text_color = db.Column(db.String(7), nullable=False, default="#ffffff")

    # Term dates (naive UTC stored; displayed/calculated in university timezone)
    autumn_term_start = db.Column(db.DateTime, nullable=True)
    autumn_term_end = db.Column(db.DateTime, nullable=True)
    spring_term_start = db.Column(db.DateTime, nullable=True)
    spring_term_end = db.Column(db.DateTime, nullable=True)
    summer_term_start = db.Column(db.DateTime, nullable=True)  # nullable — not all unis have summer term
    summer_term_end = db.Column(db.DateTime, nullable=True)

    # Logo fetching status (absorbed from UniversityLogo)
    logo_status = db.Column(db.String(20), nullable=False, default="pending")  # 'pending', 'fetched', 'no_logo'
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    # WeeklySnapshot is a DIRECT child of UniversityConfig (not of Season).
    # Weeks are calendar weeks (Mon–Sun) and are independent of term boundaries —
    # a week can straddle two seasons, so it cannot belong to one Season.
    # SeasonalSnapshot IS a child of Season (via season_id FK).
    seasons = db.relationship("Season", backref="university", lazy=True)
    weekly_snapshots = db.relationship(
        "WeeklySnapshot",
        foreign_keys="WeeklySnapshot.university_domain",
        primaryjoin="UniversityConfig.domain == WeeklySnapshot.university_domain",
        backref="university_config",
        lazy=True,
    )

    def __repr__(self):
        return f"<UniversityConfig domain={self.domain}>"
```

**Step 3 — Add `Season` model** after `UniversityConfig`:

```python
# ──────────────────────────────────────────────
# Season Model
# ──────────────────────────────────────────────
class Season(db.Model):
    __tablename__ = "seasons"

    id = db.Column(db.Integer, primary_key=True)
    university_domain = db.Column(
        db.String(100), db.ForeignKey("university_configs.domain"), nullable=False, index=True
    )
    name = db.Column(db.String(100), nullable=False)  # e.g. "Autumn Term 2026"
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    is_complete = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    seasonal_snapshots = db.relationship("SeasonalSnapshot", backref="season", lazy=True)

    def __repr__(self):
        return f"<Season id={self.id} name={self.name}>"
```

**Step 4 — Add `WeeklySnapshot` model** after `Season`:

```python
# ──────────────────────────────────────────────
# Weekly Leaderboard Snapshot
# ──────────────────────────────────────────────
class WeeklySnapshot(db.Model):
    __tablename__ = "weekly_snapshots"
    __table_args__ = (
        db.UniqueConstraint("university_domain", "week_start", "rank", name="uq_weekly_snapshot_rank"),
        db.Index("ix_weekly_snapshot_domain_week", "university_domain", "week_start"),
    )

    id = db.Column(db.Integer, primary_key=True)
    university_domain = db.Column(
        db.String(100), db.ForeignKey("university_configs.domain"), nullable=False
    )
    week_start = db.Column(db.DateTime, nullable=False)  # Monday 00:00 UTC
    week_end = db.Column(db.DateTime, nullable=False)    # Sunday 23:59:59 UTC
    rank = db.Column(db.Integer, nullable=False)         # 1–10

    # Frozen at archive time — never recalculated
    display_name = db.Column(db.String(80), nullable=False)
    kg_saved = db.Column(db.Numeric(10, 2, asdecimal=False), nullable=False)
    transaction_count = db.Column(db.Integer, nullable=False)

    # Nullable FK for GDPR deletion (nulled if user deletes account post-snapshot)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    archived_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", backref=db.backref("weekly_snapshots", lazy=True))

    def __repr__(self):
        return f"<WeeklySnapshot domain={self.university_domain} week={self.week_start} rank={self.rank}>"
```

**Step 5 — Add `SeasonalSnapshot` model** after `WeeklySnapshot`:

```python
# ──────────────────────────────────────────────
# Seasonal Leaderboard Snapshot (Hall of Fame)
# ──────────────────────────────────────────────
class SeasonalSnapshot(db.Model):
    __tablename__ = "seasonal_snapshots"
    __table_args__ = (
        db.UniqueConstraint("season_id", "rank", name="uq_seasonal_snapshot_rank"),
        db.Index("ix_seasonal_snapshot_domain", "university_domain"),
    )

    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey("seasons.id"), nullable=False)
    university_domain = db.Column(
        db.String(100), db.ForeignKey("university_configs.domain"), nullable=False
    )
    rank = db.Column(db.Integer, nullable=False)         # 1–10

    # Frozen at archive time — never recalculated
    display_name = db.Column(db.String(80), nullable=False)
    kg_saved = db.Column(db.Numeric(10, 2, asdecimal=False), nullable=False)
    transaction_count = db.Column(db.Integer, nullable=False)

    # Nullable FK for GDPR deletion
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    archived_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", backref=db.backref("seasonal_snapshots", lazy=True))

    def __repr__(self):
        return f"<SeasonalSnapshot season_id={self.season_id} rank={self.rank}>"
```

**Step 6 — Modify `User` model**: Add `show_on_leaderboard` field after `deletion_pending_until`:

```python
show_on_leaderboard = db.Column(db.Boolean, default=True, nullable=False, server_default=sa.text('true'))
```

**Step 7 — Modify `Item` model**: Add `sold_at` field after `is_sold`:

```python
sold_at = db.Column(db.DateTime, nullable=True, default=None)
```

**Step 8 — Modify `User.anonymise()`**: Extend the method to handle leaderboard snapshots.
Add the following block **inside** `anonymise()`, before `db.session.commit()` is called by the caller:

```python
# Sever and mask leaderboard snapshot entries (GDPR: preserve history, erase identity)
# Assign a deterministic eco-title based on the rank position.
#
# IMPORTANT: WeeklySnapshot, SeasonalSnapshot, and ECO_TITLES are defined in the SAME
# file (app/models.py) as User.anonymise(). Do NOT add an import — it will cause a
# circular import error. Reference them directly.

weekly_entries = WeeklySnapshot.query.filter_by(user_id=self.id).all()
for entry in weekly_entries:
    title_base = ECO_TITLES[entry.rank - 1] if entry.rank <= len(ECO_TITLES) else "Eco Hero"
    entry.display_name = f"{title_base} #{entry.rank}"
    entry.user_id = None

seasonal_entries = SeasonalSnapshot.query.filter_by(user_id=self.id).all()
for entry in seasonal_entries:
    title_base = ECO_TITLES[entry.rank - 1] if entry.rank <= len(ECO_TITLES) else "Eco Hero"
    entry.display_name = f"{title_base} #{entry.rank}"
    entry.user_id = None
```


---

### Phase 3 — Alembic Migration

Create a new migration file. The migration must:

1. **Rename** `university_logos` → `university_configs`
2. **Add columns** to `university_configs`:
   - `subdomain_slug` VARCHAR(50) UNIQUE NOT NULL (backfill: derive from domain, e.g. `brookes.ac.uk` → `brookes`)
   - `display_name` VARCHAR(200) NOT NULL (backfill: use `subdomain_slug.title()` as placeholder)
   - `email_domain` VARCHAR(100) NOT NULL (backfill: same as `domain`)
   - `timezone` VARCHAR(50) NOT NULL DEFAULT `'Europe/London'`
   - `brand_color` VARCHAR(7) NOT NULL DEFAULT `'#1a1a2e'`
   - `brand_text_color` VARCHAR(7) NOT NULL DEFAULT `'#ffffff'`
   - `autumn_term_start`, `autumn_term_end`, `spring_term_start`, `spring_term_end` — DATETIME nullable
   - `summer_term_start`, `summer_term_end` — DATETIME nullable
3. **Create** `seasons` table
4. **Create** `weekly_snapshots` table
5. **Create** `seasonal_snapshots` table
6. **Add column** `sold_at` DATETIME nullable to `items`
7. **Add column** `show_on_leaderboard` BOOLEAN NOT NULL DEFAULT TRUE to `users`

Seed two `UniversityConfig` rows in the migration's `upgrade()` function to replace the hardcoded config:

```python
from sqlalchemy.sql import table, column
import sqlalchemy as sa

uni_configs = table(
    'university_configs',
    column('domain', sa.String),
    column('subdomain_slug', sa.String),
    column('display_name', sa.String),
    column('email_domain', sa.String),
    column('timezone', sa.String),
    column('brand_color', sa.String),
    column('brand_text_color', sa.String),
    column('logo_status', sa.String),
)

op.bulk_insert(uni_configs, [
    {
        'domain': 'brookes.ac.uk',
        'subdomain_slug': 'brookes',
        'display_name': 'Oxford Brookes University',
        'email_domain': 'brookes.ac.uk',
        'timezone': 'Europe/London',
        'brand_color': '#002855',
        'brand_text_color': '#ffffff',
        'logo_status': 'pending',
    },
    {
        'domain': 'oxford.ac.uk',
        'subdomain_slug': 'oxford',
        'display_name': 'University of Oxford',
        'email_domain': 'oxford.ac.uk',
        'timezone': 'Europe/London',
        'brand_color': '#002147',
        'brand_text_color': '#ffffff',
        'logo_status': 'pending',
    },
])
```

---

### Phase 4 — Flask-Caching Setup

#### [MODIFY] `requirements.txt`

Add:
```
Flask-Caching==2.3.0
```

#### [MODIFY] `app/__init__.py`

**Step 1** — Add import and cache initialisation at the top of the file, alongside the other extensions:

```python
from flask_caching import Cache
cache = Cache()
```

**Step 2** — In `create_app()`, after `limiter.init_app(app)`, add:

```python
# Configure Flask-Caching (SimpleCache for single-process; swap to RedisCache via CACHE_TYPE env var)
cache_config = {
    "CACHE_TYPE": os.environ.get("CACHE_TYPE", "SimpleCache"),
    "CACHE_DEFAULT_TIMEOUT": 300,  # 5 minutes
}
if os.environ.get("CACHE_TYPE") == "RedisCache":
    cache_config["CACHE_REDIS_URL"] = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
app.config.from_mapping(cache_config)
cache.init_app(app)
```

**Step 3** — Remove the hand-rolled `_stats_cache` dict and `_stats_cache_lock` from the top of `__init__.py`.
Replace the landing page stats block in the `index()` route with cache-decorated helper functions (see Phase 6).

---

### Phase 5 — UniversityConfig as Single Source of Truth

#### [MODIFY] `app/__init__.py`

**Step 1 — Replace `UniversityLogo` import** on line 111:

```python
# OLD:
from app.models import User, Item, CancellationRecord, Message, Notification, UniversityLogo

# NEW:
from app.models import User, Item, CancellationRecord, Message, Notification, UniversityConfig
```

**Step 2 — Replace `SUBDOMAIN_UNIVERSITY_MAP` usage** in `detect_subdomain()`:

The current code calls `app.config.get("SUBDOMAIN_UNIVERSITY_MAP", {})`. Replace ALL occurrences of this with a helper function that reads from DB, cached in memory per app instance:

Add this helper function near the top of `create_app()`, before the `before_request` hooks:

```python
def get_subdomain_map():
    """
    Returns the subdomain → domain mapping, loaded from UniversityConfig table.
    Falls back to config.py hardcoded map if DB is unavailable (e.g. during migrations).
    Result is cached in app context for the lifetime of the process.
    """
    cached = app.extensions.get("_subdomain_map")
    if cached is not None:
        return cached
    try:
        rows = UniversityConfig.query.with_entities(
            UniversityConfig.subdomain_slug, UniversityConfig.domain
        ).all()
        result = {row.subdomain_slug: row.domain for row in rows}
    except Exception:
        result = app.config.get("SUBDOMAIN_UNIVERSITY_MAP", {})
    app.extensions["_subdomain_map"] = result
    return result
```

Replace every `app.config.get("SUBDOMAIN_UNIVERSITY_MAP", {})` call in `__init__.py` with `get_subdomain_map()`.

> [!NOTE]
> The `app.extensions["_subdomain_map"]` cache is intentionally process-level (not request-level).
> When a new university is added via admin panel, call `app.extensions.pop("_subdomain_map", None)`
> to invalidate and force a DB reload on the next request.

**Step 3 — Replace brand color helpers** in `inject_logo_helpers()`:

Replace the hardcoded `colors` dict in `get_brand_color()` and `get_brand_text_color()` with DB lookups:

```python
def get_brand_color(domain):
    if not domain:
        return "var(--color-primary-muted)"
    config = UniversityConfig.query.filter_by(domain=domain).first()
    return config.brand_color if config else "var(--color-primary-muted)"

def get_brand_text_color(domain):
    if not domain:
        return "var(--color-primary)"
    config = UniversityConfig.query.filter_by(domain=domain).first()
    return config.brand_text_color if config else "var(--color-primary)"
```

**Step 4 — Replace `UniversityLogo` reference** in `get_logo_status()` inside `inject_logo_helpers()`:

```python
# OLD:
from app.models import UniversityLogo
logo_rec = UniversityLogo.query.filter_by(domain=domain).first()

# NEW:
logo_rec = UniversityConfig.query.filter_by(domain=domain).first()
```

**Step 5 — Make landing page stats dynamic**.

In the `index()` route, replace the hardcoded Brookes/Oxford queries with a dynamic loop.

> [!IMPORTANT]
> `@cache.cached` on a nested function defined inside a route **does not work** in Flask-Caching.
> Use `cache.get` / `cache.set` directly, exactly as shown below.

```python
# Inside the index() route, replace the hardcoded stats block with:
landing_stats = cache.get("landing_stats")
if landing_stats is None:
    from app.models import Item, User, UniversityConfig
    configs = UniversityConfig.query.all()
    total_saved = db.session.query(db.func.sum(Item.kg_saved)).filter(
        Item.is_sold == True
    ).scalar() or 0.0

    universities = []
    for cfg in configs:
        active_count = Item.query.filter_by(
            is_sold=False, buyer_id=None, university_domain=cfg.domain
        ).count()
        kg_saved = db.session.query(db.func.sum(Item.kg_saved)).filter(
            Item.is_sold == True, Item.university_domain == cfg.domain
        ).scalar() or 0.0
        students = User.query.filter_by(
            university_domain=cfg.domain, is_verified=True
        ).count()
        circulated = Item.query.filter(Item.university_domain == cfg.domain).count()
        universities.append({
            "slug": cfg.subdomain_slug,
            "domain": cfg.domain,
            "name": cfg.display_name,
            "active_count": active_count,
            "kg_saved": float(kg_saved),
            "students": students,
            "circulated": circulated,
        })

    landing_stats = {
        "total_saved": float(total_saved),
        "total_co2": float(total_saved) * 2.5,
        "universities": universities,
    }
    cache.set("landing_stats", landing_stats, timeout=300)

# Pass landing_stats to the template:
# total_saved = landing_stats["total_saved"]
# universities = landing_stats["universities"]  etc.
```

#### [MODIFY] `app/config.py`

Keep `SUBDOMAIN_UNIVERSITY_MAP` in config as a hardcoded **fallback only** (used if DB is unavailable during startup). Add the following comment:

```python
# FALLBACK ONLY — runtime routing reads from UniversityConfig DB table.
# This is used only if the DB is unavailable (e.g., during initial migration).
SUBDOMAIN_UNIVERSITY_MAP = {
    "brookes": "brookes.ac.uk",
    "oxford": "oxford.ac.uk",
}
```

Also add the feature flag:

```python
FEATURE_MULTI_UNIVERSITY = os.environ.get("FEATURE_MULTI_UNIVERSITY", "false").lower() == "true"
```

#### [MODIFY] `app/utils/logo_downloader.py`

Replace `UniversityLogo` import and usage with `UniversityConfig`.

---

### Phase 6 — Leaderboard Utility Functions

#### [NEW] `app/utils/leaderboard.py`

Create this file. It contains all shared query and boundary logic:

```python
"""
Reuni — Leaderboard Query Utilities
"""
from datetime import datetime, timezone, timedelta
import zoneinfo

from app import db
from app.models import Item, User, Season, WeeklySnapshot, SeasonalSnapshot

# Do NOT hardcode a timezone here. Week boundaries are always computed
# using the individual university's timezone from UniversityConfig.timezone.
SNAPSHOT_TOP_N = 10
HOF_TOP_N = 3
WEEKLY_HOF_HISTORY = 4  # How many past weeks to show in Weekly Hall of Fame


def get_current_week_boundaries(university_timezone="Europe/London"):
    """
    Returns (week_start, week_end) as naive UTC datetimes for the current
    calendar week (Monday 00:00 → Sunday 23:59:59.999999) in the given
    university's LOCAL timezone.

    university_timezone: IANA timezone string from UniversityConfig.timezone
    e.g. "Europe/London", "Asia/Dubai", "Africa/Cairo"

    Always pass uni_config.timezone explicitly. Never call with no arguments
    unless you genuinely mean London time (e.g. in tests).
    """
    uni_tz = zoneinfo.ZoneInfo(university_timezone)
    now_local = datetime.now(uni_tz)
    monday = now_local - timedelta(days=now_local.weekday())
    week_start_local = monday.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end_local = week_start_local + timedelta(days=7) - timedelta(microseconds=1)

    week_start_utc = week_start_local.astimezone(timezone.utc).replace(tzinfo=None)
    week_end_utc = week_end_local.astimezone(timezone.utc).replace(tzinfo=None)
    return week_start_utc, week_end_utc


def get_live_leaderboard(university_domain, period_start, period_end, limit=10):
    """
    Aggregates live leaderboard rankings from the items table for a given
    university and time period.

    Returns list of dicts: [
        {rank, user_id, display_name, kg_saved, transaction_count}
    ]

    Applies tiebreakers: SUM(kg_saved) DESC, COUNT(item_id) DESC, MIN(sold_at) ASC.
    Only includes users with role='student', is_active=True, show_on_leaderboard=True,
    and at least 1 completed transaction in the period.
    """
    from sqlalchemy import func

    rows = (
        db.session.query(
            User.id.label("user_id"),
            User.name.label("display_name"),
            func.sum(Item.kg_saved).label("kg_saved"),
            func.count(Item.id).label("transaction_count"),
            func.min(Item.sold_at).label("first_sold_at"),
        )
        .join(Item, Item.seller_id == User.id)
        .filter(
            Item.is_sold == True,
            Item.sold_at >= period_start,
            Item.sold_at <= period_end,
            Item.university_domain == university_domain,
            User.is_active == True,
            User.role == "student",
            User.show_on_leaderboard == True,
        )
        .group_by(User.id, User.name)
        .order_by(
            func.sum(Item.kg_saved).desc(),
            func.count(Item.id).desc(),
            func.min(Item.sold_at).asc(),
        )
        .limit(limit)
        .all()
    )

    results = []
    for i, row in enumerate(rows, start=1):
        results.append({
            "rank": i,
            "user_id": row.user_id,
            "display_name": row.display_name,
            "kg_saved": float(row.kg_saved),
            "transaction_count": row.transaction_count,
        })
    return results


def get_current_user_rank(user_id, university_domain, period_start, period_end):
    """
    Returns the rank and kg_saved of the given user for the specified period,
    or None if the user has no transactions in the period or is opted out.
    Returns dict: {rank, kg_saved, transaction_count} or None.
    """
    from sqlalchemy import func, and_, or_
    from decimal import Decimal

    # Get the user's aggregated stats
    user_stats = (
        db.session.query(
            func.sum(Item.kg_saved).label("kg_saved"),
            func.count(Item.id).label("transaction_count"),
            func.min(Item.sold_at).label("first_sold_at"),
        )
        .join(User, User.id == Item.seller_id)
        .filter(
            Item.is_sold == True,
            Item.sold_at >= period_start,
            Item.sold_at <= period_end,
            Item.university_domain == university_domain,
            Item.seller_id == user_id,
            User.is_active == True,
            User.show_on_leaderboard == True,
        )
        .first()
    )

    if not user_stats or not user_stats.kg_saved:
        return None

    # Keep as Decimal to avoid float precision issues in SQL comparisons
    # Item.kg_saved is Numeric(10, 2) — Decimal matches the column type exactly
    user_kg = Decimal(str(user_stats.kg_saved))
    user_tx = user_stats.transaction_count
    user_first = user_stats.first_sold_at

    # Count users ranked strictly above this user using a subquery.
    # This pattern is unambiguous: count rows in the subquery = count of users beating us.
    subq = (
        db.session.query(User.id)
        .join(Item, Item.seller_id == User.id)
        .filter(
            Item.is_sold == True,
            Item.sold_at >= period_start,
            Item.sold_at <= period_end,
            Item.university_domain == university_domain,
            User.is_active == True,
            User.role == "student",
            User.show_on_leaderboard == True,
        )
        .group_by(User.id)
        .having(
            or_(
                func.sum(Item.kg_saved) > user_kg,
                and_(
                    func.sum(Item.kg_saved) == user_kg,
                    func.count(Item.id) > user_tx,
                ),
                and_(
                    func.sum(Item.kg_saved) == user_kg,
                    func.count(Item.id) == user_tx,
                    func.min(Item.sold_at) < user_first,
                ),
            )
        )
        .subquery()
    )
    rank_above = db.session.query(func.count()).select_from(subq).scalar() or 0

    return {
        "rank": rank_above + 1,
        "kg_saved": float(user_kg),
        "transaction_count": user_tx,
    }


def get_active_season(university_domain):
    """Returns the currently active Season for a university, or None."""
    return Season.query.filter_by(
        university_domain=university_domain,
        is_active=True,
        is_complete=False,
    ).first()


def get_cross_university_standings(season):
    """
    Returns live cross-university kg rankings for the given season.
    Aggregated from items table — no personal data.
    Returns list of dicts: [{university_domain, display_name, total_kg, rank}]
    Only used when FEATURE_MULTI_UNIVERSITY=True.
    """
    from app.models import UniversityConfig
    from sqlalchemy import func

    rows = (
        db.session.query(
            Item.university_domain,
            func.sum(Item.kg_saved).label("total_kg"),
        )
        .filter(
            Item.is_sold == True,
            Item.sold_at >= season.start_date,
            Item.sold_at <= season.end_date,
        )
        .group_by(Item.university_domain)
        .order_by(func.sum(Item.kg_saved).desc())
        .all()
    )

    # Enrich with display names
    domain_names = {
        cfg.domain: cfg.display_name
        for cfg in UniversityConfig.query.all()
    }

    results = []
    for i, row in enumerate(rows, start=1):
        results.append({
            "rank": i,
            "university_domain": row.university_domain,
            "display_name": domain_names.get(row.university_domain, row.university_domain),
            "total_kg": float(row.total_kg),
        })
    return results
```

---

### Phase 7 — Leaderboard Routes

#### [NEW] `app/routes/leaderboard.py`

> [!IMPORTANT]
> `@cache.cached` with a `lambda` key_prefix does **not** work in Flask-Caching.
> Use `cache.get` / `cache.set` directly for dynamic cache keys. The pattern below is correct.

```python
"""
Reuni — Leaderboard & Hall of Fame Routes
"""
from flask import Blueprint, render_template, g, current_app
from flask_login import login_required, current_user
from app.utils.decorators import verified_required
from app import db, cache, limiter
from app.models import Season, WeeklySnapshot, SeasonalSnapshot
from app.utils.leaderboard import (
    get_current_week_boundaries,
    get_live_leaderboard,
    get_current_user_rank,
    get_active_season,
    get_cross_university_standings,
    WEEKLY_HOF_HISTORY,
    HOF_TOP_N,
)

leaderboard_bp = Blueprint("leaderboard", __name__)


@leaderboard_bp.route("/leaderboard")
@login_required
@verified_required
@limiter.limit("30 per minute")
def leaderboard():
    """Live leaderboard — Weekly and Seasonal tabs."""
    uni_domain = g.current_uni_domain

    # Fetch university config to get the correct local timezone for week boundaries.
    # Do NOT hardcode Europe/London here — the university may be in any country.
    from app.models import UniversityConfig
    uni_config = UniversityConfig.query.filter_by(domain=uni_domain).first()
    uni_timezone = uni_config.timezone if uni_config else "Europe/London"

    # ── Weekly (cache.get/set pattern — lambda key_prefix is NOT supported) ──
    week_start, week_end = get_current_week_boundaries(uni_timezone)
    weekly_cache_key = f"leaderboard_weekly_{uni_domain}_{week_start.date()}"
    weekly_rankings = cache.get(weekly_cache_key)
    if weekly_rankings is None:
        weekly_rankings = get_live_leaderboard(uni_domain, week_start, week_end)
        cache.set(weekly_cache_key, weekly_rankings, timeout=300)

    user_weekly_rank = get_current_user_rank(current_user.id, uni_domain, week_start, week_end)

    # ── Seasonal ──
    active_season = get_active_season(uni_domain)
    seasonal_rankings = []
    user_seasonal_rank = None

    if active_season:
        seasonal_cache_key = f"leaderboard_seasonal_{uni_domain}_{active_season.id}"
        seasonal_rankings = cache.get(seasonal_cache_key)
        if seasonal_rankings is None:
            seasonal_rankings = get_live_leaderboard(
                uni_domain, active_season.start_date, active_season.end_date
            )
            cache.set(seasonal_cache_key, seasonal_rankings, timeout=300)

        user_seasonal_rank = get_current_user_rank(
            current_user.id, uni_domain, active_season.start_date, active_season.end_date
        )

    # ── Cross-university (feature-flagged) ──
    multi_uni_enabled = current_app.config.get("FEATURE_MULTI_UNIVERSITY", False)
    cross_uni_standings = []
    if multi_uni_enabled and active_season:
        cross_cache_key = f"leaderboard_crossuni_{active_season.id}"
        cross_uni_standings = cache.get(cross_cache_key)
        if cross_uni_standings is None:
            cross_uni_standings = get_cross_university_standings(active_season)
            cache.set(cross_cache_key, cross_uni_standings, timeout=300)

    return render_template(
        "leaderboard/leaderboard.html",
        weekly_rankings=weekly_rankings,
        user_weekly_rank=user_weekly_rank,
        week_start=week_start,
        week_end=week_end,
        seasonal_rankings=seasonal_rankings,
        user_seasonal_rank=user_seasonal_rank,
        active_season=active_season,
        cross_uni_standings=cross_uni_standings,
        multi_uni_enabled=multi_uni_enabled,
    )


@leaderboard_bp.route("/hall-of-fame")
@login_required
@verified_required
@limiter.limit("30 per minute")
def hall_of_fame():
    """Hall of Fame — frozen historical snapshots."""
    uni_domain = g.current_uni_domain

    # ── Weekly Hall of Fame ──
    # Limit to last WEEKLY_HOF_HISTORY distinct weeks at the DB level.
    # Get the most recent N distinct week_start values first, then fetch their entries.
    # Do NOT fetch all rows and slice in Python — that's inefficient and fragile.
    from sqlalchemy import distinct
    recent_week_starts = (
        db.session.query(distinct(WeeklySnapshot.week_start))
        .filter_by(university_domain=uni_domain)
        .order_by(WeeklySnapshot.week_start.desc())
        .limit(WEEKLY_HOF_HISTORY)
        .all()
    )
    recent_week_starts = [row[0] for row in recent_week_starts]

    weekly_hof = []
    for ws in recent_week_starts:
        entries = (
            WeeklySnapshot.query
            .filter_by(university_domain=uni_domain, week_start=ws)
            .filter(WeeklySnapshot.rank <= HOF_TOP_N)
            .order_by(WeeklySnapshot.rank)
            .all()
        )
        weekly_hof.append({"week_start": ws, "entries": entries})

    # ── Seasonal / Grand Hall of Fame (all completed seasons, top 3 each) ──
    completed_seasons = (
        Season.query
        .filter_by(university_domain=uni_domain, is_complete=True)
        .order_by(Season.end_date.desc())
        .all()
    )

    seasonal_hof = []
    for season in completed_seasons:
        entries = (
            SeasonalSnapshot.query
            .filter_by(season_id=season.id)
            .filter(SeasonalSnapshot.rank <= HOF_TOP_N)
            .order_by(SeasonalSnapshot.rank)
            .all()
        )
        # University total kg for the season (computed from items — includes deleted users)
        from app.models import Item
        from sqlalchemy import func
        total_kg = db.session.query(func.sum(Item.kg_saved)).filter(
            Item.is_sold == True,
            Item.sold_at >= season.start_date,
            Item.sold_at <= season.end_date,
            Item.university_domain == uni_domain,
        ).scalar() or 0.0

        seasonal_hof.append({
            "season": season,
            "entries": entries,
            "total_kg": float(total_kg),
        })

    return render_template(
        "leaderboard/hall_of_fame.html",
        weekly_hof=weekly_hof,
        seasonal_hof=seasonal_hof,
    )
```

#### [MODIFY] `app/__init__.py` — Blueprint registration

> [!IMPORTANT]
> `app/routes/__init__.py` is just a package marker (65 bytes). **Do NOT add blueprint
> registration there.** All blueprints are registered in `app/__init__.py` inside `create_app()`.

In `app/__init__.py`, find the block where other blueprints are registered (around line 219-223)
and add:
```python
from app.routes.leaderboard import leaderboard_bp
app.register_blueprint(leaderboard_bp)
```

#### [MODIFY] `app/templates/base.html` — Navigation links

Add leaderboard navigation links to the nav menu. Find the navigation section and add:
```html
<a href="/leaderboard" class="nav__link">Leaderboard</a>
<a href="/hall-of-fame" class="nav__link">Hall of Fame</a>
```
Follow the exact same HTML structure and CSS class pattern as existing nav links in `base.html`.

---

### Phase 8 — Scheduler Reset Jobs

#### [MODIFY] `app/scheduler.py`

Add the following three functions and update `init_scheduler()`:

**Helper — archive snapshot:**
```python
def _archive_weekly_snapshot(app, university_domain, week_start, week_end):
    """
    Archives the top 10 users for a completed week into WeeklySnapshot.
    Idempotent: skips if snapshot for this period+domain already exists.
    Returns list of top 3 winners for notification.
    """
    from app.models import WeeklySnapshot
    from app.utils.leaderboard import get_live_leaderboard

    # Idempotency check
    existing = WeeklySnapshot.query.filter_by(
        university_domain=university_domain,
        week_start=week_start,
        rank=1,
    ).first()
    if existing:
        app.logger.warning(
            f"Weekly snapshot already exists for {university_domain} week {week_start}. Skipping."
        )
        return []

    rankings = get_live_leaderboard(university_domain, week_start, week_end, limit=10)
    if not rankings:
        app.logger.info(f"No rankings to archive for {university_domain} week {week_start}.")
        return []

    for entry in rankings:
        snapshot = WeeklySnapshot(
            university_domain=university_domain,
            week_start=week_start,
            week_end=week_end,
            rank=entry["rank"],
            user_id=entry["user_id"],
            display_name=entry["display_name"],
            kg_saved=entry["kg_saved"],
            transaction_count=entry["transaction_count"],
        )
        db.session.add(snapshot)

    return rankings[:3]  # Return top 3 for winner notifications
```

**Helper — archive seasonal snapshot:**
```python
def _archive_seasonal_snapshot(app, season):
    """
    Archives the top 10 users for a completed season into SeasonalSnapshot.
    Idempotent: skips if snapshot for this season already exists.
    Returns list of top 3 winners for notification.
    """
    from app.models import SeasonalSnapshot
    from app.utils.leaderboard import get_live_leaderboard

    existing = SeasonalSnapshot.query.filter_by(season_id=season.id, rank=1).first()
    if existing:
        app.logger.warning(f"Seasonal snapshot already exists for season {season.id}. Skipping.")
        return []

    rankings = get_live_leaderboard(
        season.university_domain, season.start_date, season.end_date, limit=10
    )
    if not rankings:
        app.logger.info(f"No rankings to archive for season {season.id}.")
        return []

    for entry in rankings:
        snapshot = SeasonalSnapshot(
            season_id=season.id,
            university_domain=season.university_domain,
            rank=entry["rank"],
            user_id=entry["user_id"],
            display_name=entry["display_name"],
            kg_saved=entry["kg_saved"],
            transaction_count=entry["transaction_count"],
        )
        db.session.add(snapshot)

    return rankings[:3]
```

**Helper — send winner notifications:**

> [!IMPORTANT]
> `flask.render_template` requires a **request context** which does not exist in the scheduler.
> Use `app.jinja_env.get_template().render()` instead — it only needs the app context.

```python
def _notify_winners(app, winners, period_label):
    """
    Sends in-app Notification and email to the top 3 winners.
    Must be called from within an app context (inside a scheduler job).
    winners: list of dicts from get_live_leaderboard (top 3 max)
    period_label: e.g. "week of 7 Jul 2026" or "Autumn Term 2026"
    """
    from app.models import Notification, User
    from app.utils.emails import send_email

    # Use jinja_env.get_template — NOT flask.render_template (requires request context)
    winner_template = app.jinja_env.get_template("emails/winner_notification.html")

    rank_labels = {1: "🥇 1st", 2: "🥈 2nd", 3: "🥉 3rd"}

    for winner in winners:
        if not winner["user_id"]:
            continue
        user = db.session.get(User, winner["user_id"])
        if not user or not user.is_active:
            continue

        rank_label = rank_labels.get(winner["rank"], f"#{winner['rank']}")
        kg = winner["kg_saved"]

        # In-app notification
        notif = Notification(
            user_id=user.id,
            title=f"You finished {rank_label} on the leaderboard!",
            content=(
                f"Congratulations! You saved {kg:.1f} kg during the {period_label} "
                f"and finished {rank_label} on the Reuni leaderboard. "
                f"Check the Hall of Fame to see your result!"
            ),
            link="/hall-of-fame",
        )
        db.session.add(notif)

        # Email notification
        try:
            email_html = winner_template.render(
                user_name=user.name,
                rank_label=rank_label,
                kg_saved=kg,
                transaction_count=winner["transaction_count"],
                period_label=period_label,
            )
            send_email(
                to_email=user.email,
                to_name=user.name,
                subject=f"You finished {rank_label} on the Reuni Leaderboard!",
                html_content=email_html,
            )
        except Exception as mail_err:
            app.logger.warning(f"Winner notification email failed for user {user.id}: {mail_err}")
```

**Weekly reset job:**

> [!IMPORTANT]
> The weekly cron must **not** be pinned to a single timezone (e.g. `Europe/London`).
> If a UAE university's week ends at Sunday 23:59 Asia/Dubai (= 19:59 UTC), a London-pinned
> Sunday 23:59 job fires 4 hours too late and archives the wrong data.
>
> Instead: run once daily at 01:00 UTC. Inside the job, loop per-university and check
> whether "yesterday in their local timezone" was Sunday. If yes, their week just ended.
> The idempotency check prevents double-archival.

```python
def run_weekly_leaderboard_reset(app):
    """
    Fires daily at 01:00 UTC.
    For each university, checks whether the week just ended in THEIR local timezone.
    If so, archives the completed week's top 10 and notifies winners.
    Idempotency: _archive_weekly_snapshot skips if snapshot already exists.
    """
    with app.app_context():
        from app import db, cache
        from app.models import UniversityConfig
        import zoneinfo
        from datetime import datetime, timezone, timedelta

        now_utc = datetime.now(timezone.utc)

        try:
            configs = UniversityConfig.query.all()
            for cfg in configs:
                uni_tz = zoneinfo.ZoneInfo(cfg.timezone)

                # What time is it right now in this university's local timezone?
                now_local = now_utc.astimezone(uni_tz)

                # "Yesterday" in their local timezone
                yesterday_local = now_local - timedelta(days=1)

                # If yesterday was NOT Sunday (weekday 6), their week hasn't ended yet.
                if yesterday_local.weekday() != 6:
                    continue

                # Compute the boundaries of the week that just ended.
                # yesterday_local is Sunday. The week ran Mon (6 days prior) → Sun (yesterday).
                monday_local = yesterday_local - timedelta(days=yesterday_local.weekday())
                week_start_local = monday_local.replace(hour=0, minute=0, second=0, microsecond=0)
                week_end_local = week_start_local + timedelta(days=7) - timedelta(microseconds=1)

                week_start_utc = week_start_local.astimezone(timezone.utc).replace(tzinfo=None)
                week_end_utc = week_end_local.astimezone(timezone.utc).replace(tzinfo=None)

                winners = _archive_weekly_snapshot(app, cfg.domain, week_start_utc, week_end_utc)
                period_label = f"week of {week_start_utc.strftime('%-d %b %Y')}"
                _notify_winners(app, winners, period_label)
                # Invalidate cache so next page load reflects final standings
                cache.delete(f"leaderboard_weekly_{cfg.domain}_{week_start_utc.date()}")

            db.session.commit()
            app.logger.info("Weekly leaderboard check completed.")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Weekly leaderboard reset error: {e}", exc_info=True)
        finally:
            db.session.remove()
```

**Seasonal reset job:**
```python
def run_seasonal_leaderboard_reset(app):
    """
    Fires daily at 23:59 (Europe/London) and checks if any season ended today.
    Archives completed seasons and marks them as complete.
    """
    with app.app_context():
        from app import db
        from app.models import Season
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        try:
            # Find seasons that ended today (end_date <= now) and are still marked active
            ending_seasons = Season.query.filter(
                Season.is_active == True,
                Season.is_complete == False,
                Season.end_date <= now,
            ).all()

            for season in ending_seasons:
                winners = _archive_seasonal_snapshot(app, season)
                season.is_active = False
                season.is_complete = True
                period_label = season.name
                _notify_winners(app, winners, period_label)
                # Invalidate seasonal and cross-uni cache
                cache.delete(f"leaderboard_seasonal_{season.university_domain}_{season.id}")
                cache.delete(f"leaderboard_crossuni_{season.id}")
                app.logger.info(f"Seasonal reset completed for season {season.id} ({season.name}).")

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Seasonal leaderboard reset error: {e}", exc_info=True)
        finally:
            db.session.remove()
```

**Update `init_scheduler()`** — add the two new jobs:

```python
# Weekly leaderboard check — runs daily at 01:00 UTC.
# Timezone logic is per-university INSIDE the job. Do not pin this to London time.
# 01:00 UTC safely covers all universities in UTC-0 and later (UK, Europe, Middle East).
scheduler.add_job(
    run_weekly_leaderboard_reset,
    'cron',
    hour=1,
    minute=0,
    timezone='UTC',
    args=[app]
)

# Seasonal reset check — daily at 01:05 UTC.
# Season end_date is stored as naive UTC in the DB, so the comparison works
# correctly regardless of timezone. Runs 5 minutes after the weekly job to
# avoid any session/lock contention.
scheduler.add_job(
    run_seasonal_leaderboard_reset,
    'cron',
    hour=1,
    minute=5,
    timezone='UTC',
    args=[app]
)
```

Verify `requirements.txt` has `apscheduler>=3.10.0`. Python 3.9+ has `zoneinfo` built in — no additional `pytz` dependency needed.

---

### Phase 9 — Admin Panel Extensions

#### [MODIFY] `app/routes/admin.py`

Add two new admin routes:

**University Config Management:**
```
GET  /admin/universities          → list all UniversityConfig rows
GET  /admin/universities/new      → form to create new UniversityConfig
POST /admin/universities/new      → save new UniversityConfig, invalidate subdomain cache
GET  /admin/universities/<id>/edit → edit form
POST /admin/universities/<id>/edit → save edits, invalidate subdomain cache
```

When saving a new or edited UniversityConfig, invalidate the subdomain map cache:
```python
current_app.extensions.pop("_subdomain_map", None)
```

**Season Management:**
```
GET  /admin/seasons               → list all seasons (filterable by university)
POST /admin/seasons/new           → create new season
POST /admin/seasons/<id>/activate → set is_active=True (deactivates other active seasons for same domain)
POST /admin/seasons/<id>/edit     → edit dates/name of a non-complete season
```

All admin routes must be gated with the existing `@admin_required` decorator pattern.

---

### Phase 10 — User Settings (Opt-Out Toggle)

#### [MODIFY] `app/__init__.py` — settings route

In the settings page handler, add a section to handle the `show_on_leaderboard` toggle:

```python
# In the POST handler for /settings
show_on_leaderboard = request.form.get("show_on_leaderboard") == "on"
current_user.show_on_leaderboard = show_on_leaderboard
```

#### [MODIFY] Settings template

Add a toggle in the Privacy section of the settings page:

```html
<div class="settings-toggle">
    <label for="show_on_leaderboard">
        <strong>Appear on the Leaderboard</strong>
        <span>Show my name and eco-impact on the campus leaderboard ranking.</span>
    </label>
    <input type="checkbox" id="show_on_leaderboard" name="show_on_leaderboard"
           {% if current_user.show_on_leaderboard %}checked{% endif %}>
</div>
```

---

### Phase 11 — New Templates

All templates must follow the existing conventions:
- Extend `base.html`
- No inline `<script>` blocks — all JS goes in `app/static/js/leaderboard.js`
- No inline `onclick` or `onchange` event handlers
- Data passed to JS via `data-*` attributes or `<script type="application/json">` blocks
- Use `csp_nonce` on any nonce-required inline styles

#### [NEW] `app/templates/leaderboard/leaderboard.html`

Content requirements:
- Three tabs: "This Week", "This Term", and (if `multi_uni_enabled`) "All Universities"
- Each tab shows a ranked table with: rank medal/number, name, kg saved, transactions
- Below the table: the current user's "You are ranked #N with X.X kg" card
- If no rankings: empty state card "No trades completed yet — be the first!"
- If no active season (seasonal tab): off-season banner with next season start date
- Weekly tab shows `week_start` – `week_end` date range in the header

#### [NEW] `app/templates/leaderboard/hall_of_fame.html`

Content requirements:
- Weekly HoF section: shows last 4 completed weeks, top 3 each. Most recent first.
- Seasonal HoF section: shows all completed seasons, top 3 podium each + university total kg
- Anonymised entries (eco-title names) render the same as normal entries

#### [NEW] `app/templates/emails/winner_notification.html`

A Jinja2 email template. Variables available: `user_name`, `rank_label`, `kg_saved`, `transaction_count`, `period_label`.

Content:
- Congratulations message with rank label and kg saved
- How many transactions they completed
- Link to `/hall-of-fame` to see their result
- Consistent with existing Reuni email style (plain HTML, no external CSS)

#### [NEW] `app/templates/admin/universities.html`

CRUD UI for `UniversityConfig` — table of existing configs, form to add/edit.

#### [NEW] `app/templates/admin/seasons.html`

List of seasons with activate/complete actions. Form to add a new season.

---

### Phase 12 — Static JS

#### [NEW] `app/static/js/leaderboard.js`

Handles:
- Tab switching between Weekly / Seasonal / Cross-University tabs
- Reads tab selection from URL hash (`#weekly`, `#seasonal`, `#universities`)
- Animates rank numbers counting up on page load
- No inline event handlers in templates — all bound via `addEventListener` in this file

---

## Verification Plan

### Automated Tests

The existing test suite is in `tests/`. Add the following test cases:

1. **`test_weekly_boundary`**: Assert that `get_current_week_boundaries()` returns correct Monday–Sunday UTC bounds for a known date, and that the bounds shift correctly across BST/GMT transitions.

2. **`test_live_leaderboard_query`**: Seed 3 users with varying `sold_at` items in the current week. Assert ranking order respects tiebreakers.

3. **`test_leaderboard_excludes_opted_out`**: User with `show_on_leaderboard=False` must not appear in results.

4. **`test_leaderboard_excludes_inactive`**: User with `is_active=False` must not appear.

5. **`test_snapshot_idempotency`**: Call `_archive_weekly_snapshot` twice for the same week+domain. Assert only one set of rows exists.

6. **`test_anonymise_clears_snapshots`**: After `user.anonymise()`, assert snapshot `user_id=None` and `display_name` matches eco-title pattern.

7. **`test_sold_at_set_on_confirm_pin`**: After a successful PIN confirmation, assert `item.sold_at` is not None and `item.claimed_at` is None.

8. **`test_leaderboard_requires_auth`**: GET `/leaderboard` without login returns 302 redirect.

### Manual Verification

1. Deploy migration with `flask db upgrade`. Confirm all new tables exist and the two seed `UniversityConfig` rows are present.
2. Add a test item, complete a sale via PIN, confirm `sold_at` is populated in the DB.
3. Visit `/leaderboard` — confirm the selling user appears in the weekly tab.
4. Toggle `show_on_leaderboard=False` in settings — confirm user disappears from leaderboard.
5. Run `run_weekly_leaderboard_reset` manually (call from Flask shell) — confirm `WeeklySnapshot` rows created.
6. Visit `/hall-of-fame` — confirm the snapshot appears under the correct week.
7. Check that `/admin/universities` CRUD works and invalidates the subdomain cache.
8. Confirm partner dashboard "recent transactions" is now ordered correctly (no null `sold_at` order issues).

---

## Open Questions / Future Roadmap

The following were intentionally deferred to the roadmap:

- Achievement/badge system (store `badges` JSON on User, populated at snapshot archival)
- Cross-university historical Hall of Fame (`UniversitySeasonSummary` table)
- Profile display name aliases for leaderboard
- Email template refactor for existing emails (OTP, password reset, PIN) — out of scope

These are already captured in `future_roadmap.md`.
