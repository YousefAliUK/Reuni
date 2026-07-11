import os
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.background import BackgroundScheduler

def anonymise_expired_accounts(app):
    """
    Cron job task function that query-anonymises users whose deletion cooldown has expired.
    Called inside an application context with proper session cleanup.
    """
    with app.app_context():
        # Deferred imports to completely eliminate circular dependency risks
        from app import db
        from app.models import User

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        try:
            # Query for inactive users whose deletion cooldown has expired (cooldown <= now)
            expired_users = User.query.filter(
                User.is_active == False,
                User.deletion_pending_until.isnot(None),
                User.deletion_pending_until <= now
            ).all()

            for user in expired_users:
                user.anonymise()

            db.session.commit()
            if expired_users:
                app.logger.info(f"GDPR Nightly Clean: Successfully anonymised {len(expired_users)} user account(s).")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"GDPR cron error during anonymisation: {e}", exc_info=True)
        finally:
            db.session.remove()  # clean connection pool


def purge_old_notifications(app):
    """
    Nightly background task:
    1. Purge read notifications older than 30 days.
    2. Purge all notifications older than 90 days.
    """
    with app.app_context():
        from app import db
        from app.models import Notification

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        try:
            # Purge read notifications older than 30 days
            thirty_days_ago = now - timedelta(days=30)
            read_deleted = Notification.query.filter(
                Notification.is_read == True,
                Notification.created_at <= thirty_days_ago
            ).delete()

            # Purge all notifications older than 90 days
            ninety_days_ago = now - timedelta(days=90)
            all_deleted = Notification.query.filter(
                Notification.created_at <= ninety_days_ago
            ).delete()

            db.session.commit()
            if read_deleted or all_deleted:
                app.logger.info(f"Notification Nightly Clean: Purged {read_deleted} read notification(s) and {all_deleted} total notification(s).")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Scheduler error during notification purge: {e}", exc_info=True)
        finally:
            db.session.remove()


def purge_old_messages(app):
    """
    Nightly background task:
    Purge messaging logs associated with transactions completed or soft-deleted more than 90 days ago.
    """
    with app.app_context():
        from app import db
        from app.models import Message, Item
        from sqlalchemy import or_

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        ninety_days_ago = now - timedelta(days=90)

        try:
            # Delete messages older than 90 days associated with sold or soft-deleted items
            deleted_messages = Message.query.filter(
                Message.created_at <= ninety_days_ago
            ).filter(
                Message.item_id.in_(
                    db.session.query(Item.id).filter(or_(Item.is_sold == True, Item.is_deleted == True))
                )
            ).delete(synchronize_session=False)

            db.session.commit()
            if deleted_messages:
                app.logger.info(f"Message Nightly Clean: Purged {deleted_messages} message(s) older than 90 days from completed/deleted transactions.")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Scheduler error during message purge: {e}", exc_info=True)
        finally:
            db.session.remove()


def _archive_weekly_snapshot(app, university_domain, week_start, week_end):
    """
    Archives the top 10 users for a completed week into WeeklySnapshot.
    Idempotent: skips if snapshot for this period+domain already exists.
    Returns list of top 3 winners for notification.
    """
    from app import db
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


def _archive_seasonal_snapshot(app, season):
    """
    Archives the top 10 users for a completed season into SeasonalSnapshot.
    Idempotent: skips if snapshot for this season already exists.
    Returns list of top 3 winners for notification.
    """
    from app import db
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


def _notify_winners(app, winners, period_label):
    """
    Sends in-app Notification and email to the top 3 winners.
    Must be called from within an app context (inside a scheduler job).
    winners: list of dicts from get_live_leaderboard (top 3 max)
    period_label: e.g. "week of 7 Jul 2026" or "Autumn Term 2026"
    """
    from app import db
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

                # Commit database changes for this university before triggering external side-effects
                try:
                    winners = _archive_weekly_snapshot(app, cfg.domain, week_start_utc, week_end_utc)
                    db.session.commit()
                except Exception as commit_err:
                    db.session.rollback()
                    app.logger.error(f"Failed to commit weekly snapshot for {cfg.domain}: {commit_err}", exc_info=True)
                    continue

                day_num = week_start_utc.day
                period_label = f"week of {day_num} {week_start_utc.strftime('%b %Y')}"
                _notify_winners(app, winners, period_label)
                # Invalidate cache so next page load reflects final standings
                cache.delete(f"leaderboard_weekly_{cfg.domain}_{week_start_utc.date()}")

            app.logger.info("Weekly leaderboard check completed.")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Weekly leaderboard reset error: {e}", exc_info=True)
        finally:
            db.session.remove()


def run_seasonal_leaderboard_reset(app):
    """
    Fires daily at 01:05 UTC.
    Checks if any season ended today.
    Archives completed seasons and marks them as complete.
    """
    with app.app_context():
        from app import db, cache
        from app.models import Season

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        try:
            # Find seasons that ended today (end_date <= now) and are still marked active
            ending_seasons = Season.query.filter(
                Season.is_active == True,
                Season.is_complete == False,
                Season.end_date <= now,
            ).all()

            for season in ending_seasons:
                # Commit database changes for this season before triggering external side-effects
                try:
                    winners = _archive_seasonal_snapshot(app, season)
                    season.is_active = False
                    season.is_complete = True
                    db.session.commit()
                except Exception as commit_err:
                    db.session.rollback()
                    app.logger.error(f"Failed to commit seasonal snapshot for season {season.id}: {commit_err}", exc_info=True)
                    continue

                period_label = season.name
                _notify_winners(app, winners, period_label)
                # Invalidate seasonal and cross-uni cache
                cache.delete(f"leaderboard_seasonal_{season.university_domain}_{season.id}")
                cache.delete(f"leaderboard_crossuni_{season.id}")
                app.logger.info(f"Seasonal reset completed for season {season.id} ({season.name}).")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Seasonal leaderboard reset error: {e}", exc_info=True)
        finally:
            db.session.remove()


def init_scheduler(app):
    """
    Initialises and starts the BackgroundScheduler to run GDPR, leaderboard, and cleanup jobs.
    """
    if app.testing:
        return

    # Gate scheduler execution (disable in multi-worker production configurations)
    if not app.config.get("SCHEDULER_ENABLED", True):
        app.logger.info("GDPR BackgroundScheduler disabled by config (SCHEDULER_ENABLED=False).")
        return

    # In debug mode, Werkzeug runs a reloader process.
    # Prevent scheduler from starting in the reloader master process.
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    scheduler = BackgroundScheduler()
    # Register jobs to run at 2:00 AM nightly
    scheduler.add_job(
        anonymise_expired_accounts,
        'cron',
        hour=2,
        minute=0,
        args=[app]
    )
    scheduler.add_job(
        purge_old_notifications,
        'cron',
        hour=2,
        minute=0,
        args=[app]
    )
    scheduler.add_job(
        purge_old_messages,
        'cron',
        hour=2,
        minute=0,
        args=[app]
    )

    # Weekly leaderboard check — runs daily at 00:10 UTC.
    scheduler.add_job(
        run_weekly_leaderboard_reset,
        'cron',
        hour=0,
        minute=10,
        timezone='UTC',
        args=[app]
    )

    # Seasonal reset check — daily at 00:15 UTC.
    scheduler.add_job(
        run_seasonal_leaderboard_reset,
        'cron',
        hour=0,
        minute=15,
        timezone='UTC',
        args=[app]
    )

    scheduler.start()
    app.logger.info("GDPR, Leaderboard & Clean BackgroundScheduler successfully started.")
