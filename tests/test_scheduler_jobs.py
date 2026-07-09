import pytest
from datetime import datetime, timezone, timedelta
from app import db
from app.models import User, Item, Season, WeeklySnapshot, SeasonalSnapshot, Notification, UniversityConfig
from app.scheduler import (
    _archive_weekly_snapshot,
    _archive_seasonal_snapshot,
    _notify_winners,
    run_weekly_leaderboard_reset,
    run_seasonal_leaderboard_reset,
)

def test_archive_weekly_snapshot(app, db_session):
    """Test weekly leaderboard archival into WeeklySnapshot."""
    with app.app_context():
        cfg = UniversityConfig(
            domain="brookes.ac.uk",
            subdomain_slug="brookes",
            display_name="Oxford Brookes University",
        )
        user = User(
            email="student@brookes.ac.uk",
            name="Alice",
            role="student",
            is_verified=True,
        )
        user.set_password("Password123!")
        db_session.session.add_all([cfg, user])
        db_session.session.commit()

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        start_date = now - timedelta(days=2)
        end_date = now + timedelta(days=2)

        item = Item(
            title="Book",
            category="Books",
            condition="Good",
            price=0.0,
            seller_id=user.id,
            is_sold=True,
            kg_saved=5.0,
            sold_at=now,
            university_domain="brookes.ac.uk",
        )
        db_session.session.add(item)
        db_session.session.commit()

        # Archive snapshot
        winners = _archive_weekly_snapshot(app, "brookes.ac.uk", start_date, end_date)
        assert len(winners) == 1
        assert winners[0]["display_name"] == "Alice"

        # Verify entry created in DB
        snapshots = WeeklySnapshot.query.filter_by(university_domain="brookes.ac.uk").all()
        assert len(snapshots) == 1
        assert snapshots[0].display_name == "Alice"
        assert snapshots[0].kg_saved == 5.0
        assert snapshots[0].rank == 1

        # Test idempotency (should skip and return empty)
        winners_dup = _archive_weekly_snapshot(app, "brookes.ac.uk", start_date, end_date)
        assert len(winners_dup) == 0

def test_archive_seasonal_snapshot(app, db_session):
    """Test seasonal leaderboard archival into SeasonalSnapshot."""
    with app.app_context():
        cfg = UniversityConfig(
            domain="brookes.ac.uk",
            subdomain_slug="brookes",
            display_name="Oxford Brookes University",
        )
        user = User(
            email="student@brookes.ac.uk",
            name="Bob",
            role="student",
            is_verified=True,
        )
        user.set_password("Password123!")
        db_session.session.add_all([cfg, user])
        db_session.session.commit()

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        season = Season(
            university_domain="brookes.ac.uk",
            name="Autumn Term 2026",
            start_date=now - timedelta(days=10),
            end_date=now + timedelta(days=10),
            is_active=True,
            is_complete=False,
        )
        db_session.session.add(season)
        db_session.session.commit()

        item = Item(
            title="Desk",
            category="Furniture",
            condition="Good",
            price=0.0,
            seller_id=user.id,
            is_sold=True,
            kg_saved=20.0,
            sold_at=now,
            university_domain="brookes.ac.uk",
        )
        db_session.session.add(item)
        db_session.session.commit()

        # Archive snapshot
        winners = _archive_seasonal_snapshot(app, season)
        assert len(winners) == 1
        assert winners[0]["display_name"] == "Bob"

        # Verify entry created in DB
        snapshots = SeasonalSnapshot.query.filter_by(season_id=season.id).all()
        assert len(snapshots) == 1
        assert snapshots[0].display_name == "Bob"
        assert snapshots[0].kg_saved == 20.0

def test_notify_winners(app, db_session):
    """Test in-app notification creation for winners."""
    with app.app_context():
        user = User(
            email="winner@brookes.ac.uk",
            name="Charlie",
            role="student",
            is_verified=True,
        )
        user.set_password("Password123!")
        db_session.session.add(user)
        db_session.session.commit()

        winners = [{
            "rank": 1,
            "user_id": user.id,
            "display_name": "Charlie",
            "kg_saved": 15.0,
            "transaction_count": 3,
        }]

        # Trigger notification sending (suppressing actual email dispatch in tests)
        _notify_winners(app, winners, "week of 12 Oct 2026")

        # Verify in-app notification was created
        notifs = Notification.query.filter_by(user_id=user.id).all()
        assert len(notifs) == 1
        assert "🥈 2nd" not in notifs[0].title
        assert "🥇 1st" in notifs[0].title
        assert "saved 15.0 kg" in notifs[0].content

def test_run_weekly_leaderboard_reset(app, db_session):
    """Test the daily check resets leadboard when yesterday was Sunday in university timezone."""
    with app.app_context():
        # Setup config with UTC+4 timezone (e.g. Dubai)
        cfg = UniversityConfig(
            domain="brookes.ac.uk",
            subdomain_slug="brookes",
            display_name="Oxford Brookes University",
            timezone="Asia/Dubai",
        )
        user = User(
            email="student@brookes.ac.uk",
            name="Alice",
            role="student",
            is_verified=True,
        )
        user.set_password("Password123!")
        db_session.session.add_all([cfg, user])
        db_session.session.commit()

        # Mock current UTC time such that it is Monday morning in Dubai (yesterday was Sunday)
        # Monday 00:10 UTC = Monday 04:10 Asia/Dubai (yesterday was Sunday)
        now_utc = datetime(2026, 10, 12, 0, 10, tzinfo=timezone.utc)
        
        # Seed an item completed last week (Sunday 11th Oct in Dubai time = UTC-4 or similar)
        sold_time = now_utc - timedelta(days=1)  # Sunday
        item = Item(
            title="Book",
            category="Books",
            condition="Good",
            price=0.0,
            seller_id=user.id,
            is_sold=True,
            kg_saved=8.0,
            sold_at=sold_time.replace(tzinfo=None),
            university_domain="brookes.ac.uk",
        )
        db_session.session.add(item)
        db_session.session.commit()

        # Mock datetime inside run_weekly_leaderboard_reset to return our mocked now_utc
        from unittest.mock import patch
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = now_utc
            # Mock ZoneInfo or let it execute standard
            run_weekly_leaderboard_reset(app)

        # Weekly snapshot should have been created since yesterday was Sunday in Dubai
        snapshots = WeeklySnapshot.query.filter_by(university_domain="brookes.ac.uk").all()
        assert len(snapshots) == 1
        assert snapshots[0].display_name == "Alice"
        assert snapshots[0].kg_saved == 8.0
