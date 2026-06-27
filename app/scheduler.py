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
    Purge messaging logs associated with transactions completed or cancelled more than 30 days ago.
    """
    with app.app_context():
        from app import db
        from app.models import Message, Item
        from sqlalchemy import or_

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        thirty_days_ago = now - timedelta(days=30)

        try:
            # Delete messages older than 30 days associated with sold or cancelled claims
            deleted_messages = Message.query.filter(
                Message.created_at <= thirty_days_ago
            ).filter(
                Message.item_id.in_(
                    db.session.query(Item.id).filter(or_(Item.is_sold == True, Item.buyer_id == None))
                )
            ).delete(synchronize_session=False)

            db.session.commit()
            if deleted_messages:
                app.logger.info(f"Message Nightly Clean: Purged {deleted_messages} message(s) older than 30 days from completed/inactive transactions.")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Scheduler error during message purge: {e}", exc_info=True)
        finally:
            db.session.remove()


def init_scheduler(app):
    """
    Initialises and starts the BackgroundScheduler to run GDPR and cleanup jobs nightly.
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
    scheduler.start()
    app.logger.info("GDPR & Clean BackgroundScheduler successfully started.")
