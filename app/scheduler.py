import os
from datetime import datetime, timezone
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

def init_scheduler(app):
    """
    Initialises and starts the BackgroundScheduler to run GDPR anonymisation job nightly.
    """
    if app.testing:
        return

    # Gate scheduler execution (disable in multi-worker production configurations)
    if not app.config.get("SCHEDULER_ENABLED", True):
        app.logger.info("GDPR BackgroundScheduler disabled by config (SCHEDULER_ENABLED=False).")
        return

    # In debug mode, Werkzeug runs a reloader process.
    # Prevent scheduler from starting in the reloader master process.
    # If app.debug is False (production), WERKZEUG_RUN_MAIN is not set, so this check will not block.
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return

    scheduler = BackgroundScheduler()
    # Register job to run at 2:00 AM nightly
    scheduler.add_job(
        anonymise_expired_accounts,
        'cron',
        hour=2,
        minute=0,
        args=[app]
    )
    scheduler.start()
    app.logger.info("GDPR BackgroundScheduler successfully started.")
