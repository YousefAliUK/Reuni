"""
Reuni — Leaderboard & Hall of Fame Routes
"""
from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, g, current_app, request
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
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)

    # Fetch university config to get the correct local timezone for week boundaries.
    uni_config = UniversityConfig.query.filter_by(domain=uni_domain).first()
    uni_timezone = uni_config.timezone if uni_config else "Europe/London"

    # ── Weekly ──
    week_start, week_end = get_current_week_boundaries(uni_timezone)
    weekly_cache_key = f"leaderboard_weekly_{uni_domain}_{week_start.date()}"
    weekly_rankings = cache.get(weekly_cache_key)
    if weekly_rankings is None:
        weekly_rankings = get_live_leaderboard(uni_domain, week_start, week_end, limit=100)
        cache.set(weekly_cache_key, weekly_rankings, timeout=300)

    user_weekly_rank = get_current_user_rank(current_user.id, uni_domain, week_start, week_end)

    # Weekly Countdown Chip Calculation
    weekly_delta = week_end - now_utc
    weekly_days = weekly_delta.days
    weekly_hours = weekly_delta.seconds // 3600
    if weekly_days > 0:
        weekly_countdown = f"Resets in {weekly_days}d {weekly_hours}h"
    else:
        weekly_countdown = f"Resets in {weekly_hours}h"

    # ── Seasonal ──
    active_season = get_active_season(uni_domain)
    seasonal_rankings = []
    user_seasonal_rank = None
    seasonal_countdown = None
    is_paused = False

    if active_season:
        seasonal_cache_key = f"leaderboard_seasonal_{uni_domain}_{active_season.id}"
        seasonal_rankings = cache.get(seasonal_cache_key)
        if seasonal_rankings is None:
            seasonal_rankings = get_live_leaderboard(
                uni_domain, active_season.start_date, active_season.end_date, limit=100
            )
            cache.set(seasonal_cache_key, seasonal_rankings, timeout=300)

        user_seasonal_rank = get_current_user_rank(
            current_user.id, uni_domain, active_season.start_date, active_season.end_date
        )

        seasonal_delta = active_season.end_date - now_utc
        seasonal_days = seasonal_delta.days
        if seasonal_days > 0:
            seasonal_countdown = f"Ends in {seasonal_days} days"
        else:
            seasonal_hours = seasonal_delta.seconds // 3600
            seasonal_countdown = f"Ends in {seasonal_hours} hours"
    else:
        # Fallback to the latest completed season for this university
        latest_season = Season.query.filter_by(
            university_domain=uni_domain
        ).order_by(Season.end_date.desc()).first()

        if latest_season:
            active_season = latest_season
            is_paused = True
            seasonal_countdown = "Season paused — resumes in September"

            # Fetch standings from SeasonalSnapshot
            seasonal_rankings = [
                {
                    "rank": snap.rank,
                    "user_id": snap.user_id,
                    "display_name": snap.display_name,
                    "kg_saved": float(snap.kg_saved),
                    "transaction_count": snap.transaction_count,
                }
                for snap in SeasonalSnapshot.query.filter_by(season_id=latest_season.id).order_by(SeasonalSnapshot.rank).all()
            ]

            # Fetch user rank from SeasonalSnapshot if exists
            user_snap = SeasonalSnapshot.query.filter_by(season_id=latest_season.id, user_id=current_user.id).first()
            if user_snap:
                user_seasonal_rank = {
                    "rank": user_snap.rank,
                    "kg_saved": float(user_snap.kg_saved),
                    "transaction_count": user_snap.transaction_count,
                }

    # ── Cross-university (feature-flagged) ──
    multi_uni_enabled = current_app.config.get("FEATURE_MULTI_UNIVERSITY", False)
    cross_uni_standings = []
    all_seasons = []
    
    if multi_uni_enabled:
        # Fetch all seasons for the current university to display in selector
        all_seasons = Season.query.filter_by(university_domain=uni_domain).order_by(Season.end_date.desc()).all()
        
        if active_season:
            cross_cache_key = f"leaderboard_crossuni_{active_season.id}"
            cross_uni_standings = cache.get(cross_cache_key)
            if cross_uni_standings is None:
                cross_uni_standings = get_cross_university_standings(active_season)
                cache.set(cross_cache_key, cross_uni_standings, timeout=300)
            
            # Enrich cross_uni_standings for main template rendering
            enriched = []
            for item in cross_uni_standings:
                enriched_item = dict(item)
                cfg = UniversityConfig.query.filter_by(domain=item["university_domain"]).first()
                enriched_item["slug"] = cfg.subdomain_slug if cfg else item["university_domain"].split('.')[0]
                enriched_item["logo_status"] = cfg.logo_status if cfg else "pending"
                enriched_item["brand_color"] = cfg.brand_color if cfg else "var(--color-primary-muted)"
                enriched_item["brand_text_color"] = cfg.brand_text_color if cfg else "var(--color-primary)"
                
                name = item["display_name"]
                words = name.split()
                if len(words) >= 2:
                    enriched_item["initials"] = "".join([w[0] for w in words[:2]]).upper()
                else:
                    enriched_item["initials"] = name[:2].upper()
                enriched.append(enriched_item)
            cross_uni_standings = enriched

    # University Display Name & Slug
    uni_display_name = uni_config.display_name if uni_config else uni_domain.split('.')[0].title()
    uni_slug = uni_config.subdomain_slug if uni_config else uni_domain.split('.')[0]

    return render_template(
        "leaderboard/leaderboard.html",
        weekly_rankings=weekly_rankings,
        user_weekly_rank=user_weekly_rank,
        week_start=week_start,
        week_end=week_end,
        weekly_countdown=weekly_countdown,
        seasonal_rankings=seasonal_rankings,
        user_seasonal_rank=user_seasonal_rank,
        active_season=active_season,
        seasonal_countdown=seasonal_countdown,
        is_paused=is_paused,
        cross_uni_standings=cross_uni_standings,
        multi_uni_enabled=multi_uni_enabled,
        all_seasons=all_seasons,
        uni_display_name=uni_display_name,
        uni_slug=uni_slug,
    )


@leaderboard_bp.route("/leaderboard/api/universities")
@login_required
@verified_required
@limiter.limit("30 per minute")
def universities_api():
    """AJAX endpoint for cross-university standings by season."""
    season_id = request.args.get("season_id", type=int)
    if not season_id:
        return {"error": "Missing season_id"}, 400

    season = Season.query.get_or_404(season_id)
    standings = get_cross_university_standings(season)
    
    # Enrich with logo slugs for rendering on frontend
    for item in standings:
        cfg = UniversityConfig.query.filter_by(domain=item["university_domain"]).first()
        item["slug"] = cfg.subdomain_slug if cfg else item["university_domain"].split('.')[0]
        item["logo_status"] = cfg.logo_status if cfg else "pending"
        item["brand_color"] = cfg.brand_color if cfg else "var(--color-primary-muted)"
        item["brand_text_color"] = cfg.brand_text_color if cfg else "var(--color-primary)"
        
        # Monogram initials
        name = item["display_name"]
        words = name.split()
        if len(words) >= 2:
            item["initials"] = "".join([w[0] for w in words[:2]]).upper()
        else:
            item["initials"] = name[:2].upper()

    return {"standings": standings}


@leaderboard_bp.route("/hall-of-fame")
@login_required
@verified_required
@limiter.limit("30 per minute")
def hall_of_fame():
    """Hall of Fame — frozen historical snapshots."""
    uni_domain = g.current_uni_domain

    # ── Weekly Hall of Fame ──
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
    current_month = None
    month_data = None

    for ws in recent_week_starts:
        winner = (
            WeeklySnapshot.query
            .filter_by(university_domain=uni_domain, week_start=ws)
            .filter(WeeklySnapshot.rank == 1)
            .first()
        )
        if not winner:
            continue

        month_str = ws.strftime("%B %Y").upper()
        if month_str != current_month:
            current_month = month_str
            month_data = {"month": month_str, "weeks": []}
            weekly_hof.append(month_data)

        # Date range formatting: e.g. "Jun 30–Jul 6"
        week_end = ws + timedelta(days=6)
        if ws.month == week_end.month:
            date_range = f"{ws.strftime('%b %d')}–{week_end.strftime('%d')}"
        else:
            date_range = f"{ws.strftime('%b %d')}–{week_end.strftime('%b %d')}"

        initials = winner.display_name[:2].upper()
        if winner.user_id and winner.user:
            initials = winner.user.name[:2].upper()

        month_data["weeks"].append({
            "date_range": date_range,
            "display_name": winner.display_name,
            "initials": initials,
            "kg_saved": float(winner.kg_saved),
            "transaction_count": winner.transaction_count,
            "user_id": winner.user_id,
        })

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

        formatted_entries = []
        for entry in entries:
            initials = entry.display_name[:2].upper()
            if entry.user_id and entry.user:
                initials = entry.user.name[:2].upper()
            formatted_entries.append({
                "rank": entry.rank,
                "display_name": entry.display_name,
                "kg_saved": float(entry.kg_saved),
                "transaction_count": entry.transaction_count,
                "user_id": entry.user_id,
                "initials": initials,
            })

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
            "entries": formatted_entries,
            "total_kg": float(total_kg),
        })

    return render_template(
        "leaderboard/hall_of_fame.html",
        weekly_hof=weekly_hof,
        seasonal_hof=seasonal_hof,
    )
