"""
Reuni — Leaderboard & Hall of Fame Routes
"""
from flask import Blueprint, render_template, g, current_app
from flask_login import login_required, current_user
from app.utils.decorators import verified_required
from app import db, cache, limiter
from app.models import Season, WeeklySnapshot, SeasonalSnapshot, UniversityConfig
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
