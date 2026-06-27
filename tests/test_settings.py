import pytest
from app.models import User, Item
from app import db

def test_settings_requires_login(client):
    """GET /settings unauthenticated should redirect to login."""
    resp = client.get("/settings", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/login" in resp.headers["Location"]

def test_settings_requires_verified(client, db_session):
    """GET /settings with unverified account should redirect to verification."""
    user = User(
        email="unverified@brookes.ac.uk",
        name="Unverified",
        is_verified=True,  # Set to True to bypass login verification block
        university_domain="brookes.ac.uk"
    )
    user.set_password("StrongPass123")
    db_session.session.add(user)
    db_session.session.commit()

    # Log in successfully
    client.post("/auth/login", data={"email": "unverified@brookes.ac.uk", "password": "StrongPass123"}, follow_redirects=True)

    # Flip to unverified directly in database to test decorator protection
    with client.application.app_context():
        u = db.session.get(User, user.id)
        u.is_verified = False
        db.session.commit()

    resp = client.get("/settings", follow_redirects=False)
    assert resp.status_code == 302
    assert "/auth/resend-verification" in resp.headers["Location"]

def test_settings_loads_authenticated(auth_client):
    """GET /settings as verified user returns 200."""
    resp = auth_client.get("/settings")
    assert resp.status_code == 200
    assert b"Settings" in resp.data
    assert b"Phone Number Settings" not in resp.data
    assert b"Change Password" in resp.data

def test_settings_password_get_redirects(auth_client):
    """GET /settings/password redirects to /settings."""
    resp = auth_client.get("/settings/password", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/settings")

def test_settings_password_success(auth_client, sample_user, app):
    """POST /settings/password successfully changes password and user remains logged in."""
    resp = auth_client.post(
        "/settings/password",
        data={
            "current_password": "StrongPass123",
            "new_password": "NewStrongPass1",
            "confirm_password": "NewStrongPass1",
        },
        follow_redirects=True
    )
    assert b"Password updated successfully." in resp.data
    
    # Verify we can access settings page directly (user is still logged in)
    resp_settings = auth_client.get("/settings")
    assert resp_settings.status_code == 200

def test_settings_password_wrong_current(auth_client):
    """POST /settings/password with wrong current password is rejected."""
    resp = auth_client.post(
        "/settings/password",
        data={
            "current_password": "WrongPassword",
            "new_password": "NewStrongPass1",
            "confirm_password": "NewStrongPass1",
        },
        follow_redirects=True
    )
    assert b"Current password is incorrect" in resp.data

def test_settings_password_mismatch(auth_client):
    """POST /settings/password with new/confirm mismatch is rejected."""
    resp = auth_client.post(
        "/settings/password",
        data={
            "current_password": "StrongPass123",
            "new_password": "NewStrongPass1",
            "confirm_password": "DifferentNewPass",
        },
        follow_redirects=True
    )
    assert b"Passwords do not match" in resp.data

def test_settings_password_same_as_current(auth_client):
    """POST /settings/password with new same as current is rejected."""
    resp = auth_client.post(
        "/settings/password",
        data={
            "current_password": "StrongPass123",
            "new_password": "StrongPass123",
            "confirm_password": "StrongPass123",
        },
        follow_redirects=True
    )
    assert b"New password must be different" in resp.data

def test_settings_password_complexity(auth_client):
    """POST /settings/password with simple password is rejected."""
    resp = auth_client.post(
        "/settings/password",
        data={
            "current_password": "StrongPass123",
            "new_password": "simple",
            "confirm_password": "simple",
        },
        follow_redirects=True
    )
    assert b"characters long" in resp.data or b"contain at least one" in resp.data
