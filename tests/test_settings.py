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
        phone_number="+447700100099",
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
    assert b"Phone Number Settings" in resp.data
    assert b"Change Password" in resp.data

def test_settings_phone_get_redirects(auth_client):
    """GET /settings/phone redirects to /settings."""
    resp = auth_client.get("/settings/phone", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/settings")

def test_settings_password_get_redirects(auth_client):
    """GET /settings/password redirects to /settings."""
    resp = auth_client.get("/settings/password", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/settings")

def test_settings_phone_update_success(auth_client, sample_user, app):
    """POST /settings/phone updates phone number with normalization."""
    resp = auth_client.post(
        "/settings/phone",
        data={"phone_number": "07912 345678"},
        follow_redirects=True
    )
    assert b"Phone number updated successfully." in resp.data
    with app.app_context():
        user = db.session.get(User, sample_user.id)
        assert user.phone_number == "+447912345678"

def test_settings_phone_empty_blocked(auth_client, sample_user, app):
    """POST /settings/phone with empty string is rejected for all roles."""
    resp = auth_client.post(
        "/settings/phone",
        data={"phone_number": ""},
        follow_redirects=True
    )
    assert b"Phone number is required." in resp.data
    with app.app_context():
        user = db.session.get(User, sample_user.id)
        assert user.phone_number is not None
        assert user.phone_number == sample_user.phone_number

def test_settings_phone_invalid_format(auth_client, sample_user, app):
    """POST /settings/phone with invalid format is rejected."""
    resp = auth_client.post(
        "/settings/phone",
        data={"phone_number": "12345"},
        follow_redirects=True
    )
    assert b"Please enter a valid phone number" in resp.data
    with app.app_context():
        user = db.session.get(User, sample_user.id)
        assert user.phone_number == sample_user.phone_number

def test_settings_phone_same_rejected(auth_client, sample_user):
    """POST /settings/phone with same number flashes already matches."""
    resp = auth_client.post(
        "/settings/phone",
        data={"phone_number": sample_user.phone_number},
        follow_redirects=True
    )
    assert b"already your phone number" in resp.data

def test_settings_phone_duplicate_rejected(auth_client, sample_user, second_user):
    """POST /settings/phone with number owned by another user is rejected."""
    resp = auth_client.post(
        "/settings/phone",
        data={"phone_number": second_user.phone_number},
        follow_redirects=True
    )
    assert b"already registered to another account" in resp.data

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

def test_phone_guard_list_item(client, db_session):
    """User without phone number is redirected from list_item to settings."""
    user = User(
        email="nophone@brookes.ac.uk",
        name="No Phone",
        phone_number=None,
        is_verified=True,
        university_domain="brookes.ac.uk"
    )
    user.set_password("StrongPass123")
    db_session.session.add(user)
    db_session.session.commit()

    # Log in
    client.post("/auth/login", data={"email": "nophone@brookes.ac.uk", "password": "StrongPass123"}, follow_redirects=True)

    resp = client.get("/items/new", follow_redirects=True)
    assert b"Please add a phone number in Settings" in resp.data
    # Should redirect to settings page
    assert b"Phone Number Settings" in resp.data

def test_phone_guard_buy_item(client, db_session, sample_item):
    """User without phone number is redirected from buy_item to settings."""
    user = User(
        email="nophone@brookes.ac.uk",
        name="No Phone",
        phone_number=None,
        is_verified=True,
        university_domain="brookes.ac.uk"
    )
    user.set_password("StrongPass123")
    db_session.session.add(user)
    db_session.session.commit()

    # Log in
    client.post("/auth/login", data={"email": "nophone@brookes.ac.uk", "password": "StrongPass123"}, follow_redirects=True)

    # Attempt to buy/claim
    resp = client.post(f"/items/{sample_item.id}/buy", follow_redirects=True)
    assert b"Please add a phone number in Settings" in resp.data
    # Should redirect to settings page
    assert b"Phone Number Settings" in resp.data
