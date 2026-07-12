import pytest
from datetime import datetime, timezone, timedelta
from app import db
from app.models import User, UniversityConfig, Season

def test_leaderboard_routes_require_login(client):
    """Test that leaderboard routes redirect to login if unauthenticated."""
    resp1 = client.get("/leaderboard")
    assert resp1.status_code == 302
    assert "/auth/login" in resp1.headers["Location"]

    resp2 = client.get("/hall-of-fame")
    assert resp2.status_code == 302
    assert "/auth/login" in resp2.headers["Location"]

def test_leaderboard_routes_require_verification(client, db_session):
    """Test that leaderboard routes check verified status."""
    # Create verified user first to allow logging in
    user = User(
        email="unverified@brookes.ac.uk",
        name="Unverified Student",
        role="student",
        is_verified=True,
    )
    user.set_password("Password123!")
    db_session.session.add(user)
    db_session.session.commit()

    # Log in
    client.post("/auth/login", data={
        "email": "unverified@brookes.ac.uk",
        "password": "Password123!",
    })

    # Now make the user unverified in the DB and expire session cache
    user.is_verified = False
    db_session.session.commit()
    db_session.session.expire_all()

    # Accessing leaderboard should redirect / restrict access
    resp = client.get("/leaderboard")
    # In Reuni, unverified users are redirected to resend verification page
    assert resp.status_code == 302
    assert "/auth/resend-verification" in resp.headers["Location"]

def test_leaderboard_routes_success(client, db_session):
    """Test that leaderboard routes render successfully for verified users."""
    cfg = UniversityConfig(
        domain="brookes.ac.uk",
        subdomain_slug="brookes",
        display_name="Oxford Brookes University",
    )
    user = User(
        email="student@brookes.ac.uk",
        name="Verified Student",
        role="student",
        is_verified=True,
    )
    user.set_password("Password123!")
    db_session.session.add_all([cfg, user])
    db_session.session.commit()

    # Log in
    client.post("/auth/login", data={
        "email": "student@brookes.ac.uk",
        "password": "Password123!",
    })

    # Access leaderboard
    resp = client.get("/leaderboard", headers={"Host": "brookes.localhost"})
    assert resp.status_code == 200
    assert b"Leaderboard" in resp.data
    assert b"Resets in" in resp.data  # Verify countdown chip renders

    # Access hall of fame
    resp2 = client.get("/hall-of-fame", headers={"Host": "brookes.localhost"})
    assert resp2.status_code == 200
    assert b"Hall of Fame" in resp2.data

def test_universities_api_endpoint(client, db_session):
    """Test the AJAX universities standings endpoint."""
    client.application.config["FEATURE_MULTI_UNIVERSITY"] = True
    cfg1 = UniversityConfig(
        domain="brookes.ac.uk",
        subdomain_slug="brookes",
        display_name="Oxford Brookes University",
    )
    user = User(
        email="student@brookes.ac.uk",
        name="Verified Student",
        role="student",
        is_verified=True,
        university_domain="brookes.ac.uk",
    )
    user.set_password("Password123!")
    
    # Active season
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    season = Season(
        university_domain="brookes.ac.uk",
        name="Hilary 2026",
        start_date=now - timedelta(days=2),
        end_date=now + timedelta(days=2),
        is_active=True,
    )
    
    db_session.session.add_all([cfg1, user, season])
    db_session.session.commit()

    # Log in
    client.post("/auth/login", data={
        "email": "student@brookes.ac.uk",
        "password": "Password123!",
    })

    # Test missing season_id
    resp_bad = client.get("/leaderboard/api/universities")
    assert resp_bad.status_code == 400

    # Test success
    resp = client.get(f"/leaderboard/api/universities?season_id={season.id}")
    assert resp.status_code == 200
    json_data = resp.get_json()
    assert "standings" in json_data

