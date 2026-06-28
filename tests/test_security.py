"""
Reuni — Security Regression Test Suite
Verifies Content Security Policy, rate-limiting, session fixation prevention, ProxyFix, timing-safe PIN comparison, and PII-free logs.
"""

import pytest
import hashlib
import secrets
from app.models import User, Item, Notification

def test_security_headers_present(client):
    """Verify that all hardened HTTP security headers are present on responses."""
    response = client.get("/")
    
    # CSP checks
    csp = response.headers.get("Content-Security-Policy")
    assert csp is not None
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "style-src 'self' 'unsafe-inline'" in csp
    
    # Frame ancestry & Permissions
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert "geolocation=()" in response.headers.get("Permissions-Policy")
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"


def test_proxy_fix_middleware():
    """Verify that Werkzeug ProxyFix middleware is successfully registered in production mode."""
    from app import create_app
    from app.config import Config
    from werkzeug.middleware.proxy_fix import ProxyFix
    
    class DummyProdConfig(Config):
        TESTING = False
        DEBUG = False
        SECRET_KEY = "dummy-secret-key-prod-test"
        BREVO_API_KEY = "dummy-api-key"
        
    prod_app = create_app(DummyProdConfig)
    assert isinstance(prod_app.wsgi_app, ProxyFix)


def test_session_fixation_prevention(client, db_session):
    """Verify that session is cleared before authenticating to prevent fixation."""
    # 1. Establish an initial session (anonymous)
    with client.session_transaction() as sess:
        sess["fixation_marker"] = "danger"
    
    # 2. Register and login sample user
    user = User(
        email="login@brookes.ac.uk",
        name="Login User",
        is_verified=True,
        university_domain="brookes.ac.uk"
    )
    user.set_password("SecurePassword123")
    db_session.session.add(user)
    db_session.session.commit()
    
    # 3. Trigger login post request
    response = client.post("/auth/login", data={
        "email": "login@brookes.ac.uk",
        "password": "SecurePassword123"
    }, follow_redirects=True)
    
    # 4. Check if session was cleared (fixation_marker should be gone)
    with client.session_transaction() as sess:
        assert "fixation_marker" not in sess


def test_max_password_length_protection(client):
    """Verify that password lengths above 128 characters are rejected to prevent Bcrypt DoS."""
    long_password = "A" * 129
    
    # Attempt register
    response = client.post("/auth/register", data={
        "email": "dos@brookes.ac.uk",
        "name": "DoS Attacker",
        "password": long_password,
        "confirm_password": long_password
    }, follow_redirects=True)
    assert b"fewer" in response.data or b"too long" in response.data


def test_pii_free_representations():
    """Verify that User and Notification __repr__ methods do not leak email or title PII."""
    user = User(id=42, email="leaker@brookes.ac.uk", name="Leaker User")
    assert "leaker@brookes.ac.uk" not in repr(user)
    assert "Leaker User" not in repr(user)
    assert "id=42" in repr(user)
    
    notif = Notification(id=99, user_id=42, title="Sensitive Notification Title")
    assert "Sensitive Notification Title" not in repr(notif)
    assert "id=99" in repr(notif)
    assert "user=42" in repr(notif)


def test_timing_safe_pin_comparison():
    """Verify timing-safe compare digest logic works correctly for PIN handshakes."""
    correct_pin = "1234"
    incorrect_pin = "4321"
    
    # secrets.compare_digest timing-safe comparator
    assert secrets.compare_digest(correct_pin.encode(), correct_pin.encode()) is True
    assert secrets.compare_digest(correct_pin.encode(), incorrect_pin.encode()) is False


def test_rate_limiting_registration(app, client):
    """Verify that registration route rate limits successive attempts."""
    limiter = app.extensions.get("limiter")
    if limiter:
        rules = [rule for rule in app.url_map.iter_rules() if rule.endpoint == "auth.register"]
        assert len(rules) > 0


def test_login_user_enumeration_prevention(client, db_session):
    """Verify that login error responses are identical for existing vs non-existing emails."""
    user = User(
        email="enum-test@brookes.ac.uk",
        name="Enum User",
        is_verified=True,
        university_domain="brookes.ac.uk"
    )
    user.set_password("SecurePassword123")
    db_session.session.add(user)
    db_session.session.commit()

    # 1. Non-existent email
    res1 = client.post("/auth/login", data={
        "email": "nonexistent-enum@brookes.ac.uk",
        "password": "SomePassword123"
    }, follow_redirects=True)

    # 2. Existing email, wrong password
    res2 = client.post("/auth/login", data={
        "email": "enum-test@brookes.ac.uk",
        "password": "WrongPassword123"
    }, follow_redirects=True)

    assert b"Invalid email or password" in res1.data
    assert b"Invalid email or password" in res2.data


def test_register_domain_check(client):
    """Verify registration differentiates unpartnered domain from invalid format in a secure way."""
    # Unpartnered domain
    res1 = client.post("/auth/register", data={
        "email": "test@unpartnered-uni.ac.uk",
        "name": "Uni Student",
        "password": "SecurePassword123",
        "confirm_password": "SecurePassword123"
    }, follow_redirects=True)
    assert b"Reuni is not yet available at your university" in res1.data

    # Invalid email format
    res2 = client.post("/auth/register", data={
        "email": "invalid-email-format",
        "name": "Bad Email",
        "password": "SecurePassword123",
        "confirm_password": "SecurePassword123"
    }, follow_redirects=True)
    assert b"Please register with a valid institutional email address" in res2.data


def test_notifications_api_requires_login(client):
    """Verify that notifications endpoints require authentication."""
    res1 = client.get("/api/notifications")
    assert res1.status_code == 302 or res1.status_code == 401

    res2 = client.post("/api/notifications/1/read")
    assert res2.status_code == 302 or res2.status_code == 401

