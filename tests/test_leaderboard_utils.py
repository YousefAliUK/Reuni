import pytest
from datetime import datetime, timezone, timedelta
from app import db
from app.models import User, Item, Season, UniversityConfig
from app.utils.leaderboard import (
    get_current_week_boundaries,
    get_live_leaderboard,
    get_current_user_rank,
    get_active_season,
    get_cross_university_standings,
)

def test_get_current_week_boundaries():
    """Test that week boundaries represent Monday 00:00 to Sunday 23:59:59 local time."""
    start_utc, end_utc = get_current_week_boundaries()
    assert isinstance(start_utc, datetime)
    assert isinstance(end_utc, datetime)
    assert start_utc < end_utc
    # Diff should be exactly 7 days minus 1 microsecond
    diff = end_utc - start_utc
    assert diff.days == 6
    assert diff.seconds == 86399
    assert diff.microseconds == 999999

    # Test with a different timezone (e.g., Dubai - UTC+4)
    start_dubai, end_dubai = get_current_week_boundaries("Asia/Dubai")
    assert isinstance(start_dubai, datetime)
    assert isinstance(end_dubai, datetime)
    assert start_dubai < end_dubai
    diff_dubai = end_dubai - start_dubai
    assert diff_dubai.days == 6
    assert diff_dubai.seconds == 86399

def test_leaderboard_and_ranking_calculations(app, db_session):
    """Test live leaderboard rankings, tiebreakers, and individual user rank."""
    with app.app_context():
        # Setup config
        cfg = UniversityConfig(
            domain="brookes.ac.uk",
            subdomain_slug="brookes",
            display_name="Oxford Brookes University",
        )
        db_session.session.add(cfg)
        
        # Setup users
        user1 = User(
            email="student1@brookes.ac.uk",
            name="Alice",
            role="student",
            is_verified=True,
        )
        user1.set_password("Password123!")
        
        user2 = User(
            email="student2@brookes.ac.uk",
            name="Bob",
            role="student",
            is_verified=True,
        )
        user2.set_password("Password123!")

        user3 = User(
            email="student3@brookes.ac.uk",
            name="Charlie",
            role="student",
            is_verified=True,
        )
        user3.set_password("Password123!")

        db_session.session.add_all([user1, user2, user3])
        db_session.session.commit()

        # Seed items for the current week period
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        start_date = now - timedelta(days=2)
        end_date = now + timedelta(days=2)

        # Alice: 2 items, total 15.0 kg
        item1 = Item(
            title="Book",
            description="Physics",
            category="Books",
            condition="Good",
            price=0.0,
            seller_id=user1.id,
            is_sold=True,
            kg_saved=10.0,
            sold_at=now - timedelta(hours=2),
            university_domain="brookes.ac.uk",
        )
        item2 = Item(
            title="Calculator",
            description="CASIO",
            category="Electronics",
            condition="Good",
            price=0.0,
            seller_id=user1.id,
            is_sold=True,
            kg_saved=5.0,
            sold_at=now - timedelta(hours=1),
            university_domain="brookes.ac.uk",
        )

        # Bob: 2 items, total 15.0 kg (same kg, same tx count as Alice, but sold_at is later)
        item3 = Item(
            title="Chair",
            description="Desk chair",
            category="Furniture",
            condition="Good",
            price=0.0,
            seller_id=user2.id,
            is_sold=True,
            kg_saved=15.0,
            sold_at=now,
            university_domain="brookes.ac.uk",
        )

        # Charlie: 1 item, total 20.0 kg (highest kg)
        item4 = Item(
            title="Bicycle",
            description="Road bike",
            category="Sports",
            condition="Good",
            price=0.0,
            seller_id=user3.id,
            is_sold=True,
            kg_saved=20.0,
            sold_at=now - timedelta(hours=3),
            university_domain="brookes.ac.uk",
        )

        db_session.session.add_all([item1, item2, item3, item4])
        db_session.session.commit()

        # 1. Test get_live_leaderboard rankings
        rankings = get_live_leaderboard("brookes.ac.uk", start_date, end_date)
        
        # Rankings should be:
        # 1st: Charlie (20.0 kg)
        # 2nd: Alice (15.0 kg, 2 tx, first sold_at: now-2h)
        # 3rd: Bob (15.0 kg, 1 tx, first sold_at: now)
        assert len(rankings) == 3
        assert rankings[0]["display_name"] == "Charlie"
        assert rankings[0]["kg_saved"] == 20.0
        
        assert rankings[1]["display_name"] == "Alice"
        assert rankings[1]["kg_saved"] == 15.0
        assert rankings[1]["transaction_count"] == 2
        
        assert rankings[2]["display_name"] == "Bob"
        assert rankings[2]["kg_saved"] == 15.0
        assert rankings[2]["transaction_count"] == 1

        # 2. Test get_current_user_rank rankings
        char_rank = get_current_user_rank(user3.id, "brookes.ac.uk", start_date, end_date)
        assert char_rank["rank"] == 1
        assert char_rank["kg_saved"] == 20.0

        alice_rank = get_current_user_rank(user1.id, "brookes.ac.uk", start_date, end_date)
        assert alice_rank["rank"] == 2
        assert alice_rank["kg_saved"] == 15.0

        bob_rank = get_current_user_rank(user2.id, "brookes.ac.uk", start_date, end_date)
        assert bob_rank["rank"] == 3
        assert bob_rank["kg_saved"] == 15.0

def test_get_active_season(app, db_session):
    """Test checking active seasons."""
    with app.app_context():
        # Setup configs
        cfg = UniversityConfig(
            domain="brookes.ac.uk",
            subdomain_slug="brookes",
            display_name="Oxford Brookes",
        )
        db_session.session.add(cfg)
        db_session.session.commit()

        assert get_active_season("brookes.ac.uk") is None

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        season = Season(
            university_domain="brookes.ac.uk",
            name="Fall 2026",
            start_date=now - timedelta(days=5),
            end_date=now + timedelta(days=5),
            is_active=True,
            is_complete=False,
        )
        db_session.session.add(season)
        db_session.session.commit()

        active = get_active_season("brookes.ac.uk")
        assert active is not None
        assert active.id == season.id
        assert active.name == "Fall 2026"

def test_get_cross_university_standings(app, db_session):
    """Test live standings across universities."""
    with app.app_context():
        cfg1 = UniversityConfig(
            domain="brookes.ac.uk",
            subdomain_slug="brookes",
            display_name="Oxford Brookes University",
        )
        cfg2 = UniversityConfig(
            domain="oxford.ac.uk",
            subdomain_slug="oxford",
            display_name="University of Oxford",
        )
        db_session.session.add_all([cfg1, cfg2])
        
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        season = Season(
            university_domain="brookes.ac.uk",
            name="Season 1",
            start_date=now - timedelta(days=5),
            end_date=now + timedelta(days=5),
            is_active=True,
            is_complete=False,
        )
        db_session.session.add(season)
        db_session.session.commit()

        # Seed items for Brookes and Oxford
        item_brookes = Item(
            title="Brookes Item",
            description="Exchanged",
            category="Books",
            condition="Good",
            price=0.0,
            seller_id=1,  # Dummy ID
            is_sold=True,
            kg_saved=30.0,
            sold_at=now,
            university_domain="brookes.ac.uk",
        )
        item_oxford = Item(
            title="Oxford Item",
            description="Exchanged",
            category="Books",
            condition="Good",
            price=0.0,
            seller_id=2,  # Dummy ID
            is_sold=True,
            kg_saved=50.0,
            sold_at=now,
            university_domain="oxford.ac.uk",
        )
        db_session.session.add_all([item_brookes, item_oxford])
        db_session.session.commit()

        standings = get_cross_university_standings(season)
        assert len(standings) == 2
        # Rank 1 should be Oxford (50.0 kg)
        assert standings[0]["university_domain"] == "oxford.ac.uk"
        assert standings[0]["display_name"] == "University of Oxford"
        assert standings[0]["total_kg"] == 50.0
        assert standings[0]["rank"] == 1
        
        # Rank 2 should be Brookes (30.0 kg)
        assert standings[1]["university_domain"] == "brookes.ac.uk"
        assert standings[1]["display_name"] == "Oxford Brookes University"
        assert standings[1]["total_kg"] == 30.0
        assert standings[1]["rank"] == 2
