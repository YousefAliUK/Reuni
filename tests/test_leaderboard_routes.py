import pytest
from app import db
from app.models import User, UniversityConfig

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

    # Access hall of fame
    resp2 = client.get("/hall-of-fame", headers={"Host": "brookes.localhost"})
    assert resp2.status_code == 200
    assert b"Hall of Fame" in resp2.data
