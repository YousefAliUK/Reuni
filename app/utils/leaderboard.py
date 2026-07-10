"""
Reuni — Leaderboard Query Utilities
"""
from datetime import datetime, timezone, timedelta
import zoneinfo

from app import db
from app.models import Item, User, Season, WeeklySnapshot, SeasonalSnapshot

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
    Returns list of dicts: [{university_domain, display_name, total_kg, transaction_count, rank}]
    Only used when FEATURE_MULTI_UNIVERSITY=True.
    """
    from app.models import UniversityConfig
    from sqlalchemy import func

    rows = (
        db.session.query(
            Item.university_domain,
            func.sum(Item.kg_saved).label("total_kg"),
            func.count(Item.id).label("transaction_count"),
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
        active_students = User.query.filter_by(
            university_domain=row.university_domain,
            role="student",
            is_active=True,
            is_verified=True,
        ).count()
        results.append({
            "rank": i,
            "university_domain": row.university_domain,
            "display_name": domain_names.get(row.university_domain, row.university_domain),
            "total_kg": float(row.total_kg),
            "transaction_count": row.transaction_count,
            "active_students": active_students,
        })
    return results
