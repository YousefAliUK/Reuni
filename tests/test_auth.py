"""
UniCycle — Auth Route Tests
Covers registration, login, logout, and edge cases.
"""

from app.models import User


class TestRegister:

    def test_register_page_loads(self, client):
        """GET /auth/register should return 200."""
        resp = client.get("/auth/register")
        assert resp.status_code == 200
        assert b"Create Account" in resp.data

    def test_register_success(self, client, db_session):
        """Valid registration should create a user and redirect."""
        resp = client.post("/auth/register", data={
            "email": "new@university.ac.uk",
            "name": "New User",
            "phone_number": "07912345678",
            "password": "strongpass",
            "confirm_password": "strongpass",
        }, follow_redirects=False)
        assert resp.status_code == 302  # redirect

        user = User.query.filter_by(email="new@university.ac.uk").first()
        assert user is not None
        assert user.name == "New User"
        assert user.phone_number == "+447912345678"

    def test_register_duplicate_email(self, client, sample_user):
        """Registering with an existing email should flash an error."""
        resp = client.post("/auth/register", data={
            "email": "test@university.ac.uk",
            "name": "Duplicate",
            "phone_number": "07912345678",
            "password": "password123",
            "confirm_password": "password123",
        }, follow_redirects=True)
        assert b"already exists" in resp.data

    def test_register_password_mismatch(self, client):
        """Mismatched passwords should flash an error."""
        resp = client.post("/auth/register", data={
            "email": "mismatch@university.ac.uk",
            "name": "Mismatch",
            "phone_number": "07912345678",
            "password": "password123",
            "confirm_password": "different",
        }, follow_redirects=True)
        assert b"do not match" in resp.data

    def test_register_missing_fields(self, client):
        """Missing required fields should flash an error."""
        resp = client.post("/auth/register", data={
            "email": "",
            "name": "",
            "phone_number": "",
            "password": "",
            "confirm_password": "",
        }, follow_redirects=True)
        assert b"All fields are required" in resp.data

    def test_register_requires_phone(self, client):
        """Registration should fail when phone number is completely missing from request."""
        resp = client.post("/auth/register", data={
            "email": "phone-missing@university.ac.uk",
            "name": "No Phone",
            "password": "password123",
            "confirm_password": "password123",
        }, follow_redirects=True)
        assert b"All fields are required" in resp.data

    def test_duplicate_phone_rejected(self, client, sample_user):
        """Registering with an already used phone number should be rejected."""
        resp = client.post("/auth/register", data={
            "email": "another-email@university.ac.uk",
            "name": "Another User",
            "phone_number": sample_user.phone_number,  # duplicate phone
            "password": "password123",
            "confirm_password": "password123",
        }, follow_redirects=True)
        assert b"already linked to an account" in resp.data

    def test_register_normalises_phone(self, client, db_session):
        """Phone starting with +44 should be stored unchanged."""
        resp = client.post("/auth/register", data={
            "email": "intl@university.ac.uk",
            "name": "Intl User",
            "phone_number": "+447912345678",
            "password": "strongpass",
            "confirm_password": "strongpass",
        }, follow_redirects=False)
        assert resp.status_code == 302

        user = User.query.filter_by(email="intl@university.ac.uk").first()
        assert user is not None
        assert user.phone_number == "+447912345678"

    def test_register_rejects_invalid_phone(self, client):
        """Garbage phone input should be rejected after normalisation."""
        resp = client.post("/auth/register", data={
            "email": "bad-phone@university.ac.uk",
            "name": "Bad Phone",
            "phone_number": "abc123",
            "password": "strongpass",
            "confirm_password": "strongpass",
        }, follow_redirects=True)
        assert b"valid phone number" in resp.data


class TestLogin:

    def test_login_page_loads(self, client):
        """GET /auth/login should return 200."""
        resp = client.get("/auth/login")
        assert resp.status_code == 200
        assert b"Log In" in resp.data

    def test_login_success(self, client, sample_user):
        """Valid credentials should redirect (302)."""
        resp = client.post("/auth/login", data={
            "email": "test@university.ac.uk",
            "password": "password123",
        }, follow_redirects=False)
        assert resp.status_code == 302

    def test_login_invalid_credentials(self, client, sample_user):
        """Wrong password should flash an error."""
        resp = client.post("/auth/login", data={
            "email": "test@university.ac.uk",
            "password": "wrongpassword",
        }, follow_redirects=True)
        assert b"Invalid email or password" in resp.data

    def test_login_nonexistent_user(self, client):
        """Non-existent email should flash an error."""
        resp = client.post("/auth/login", data={
            "email": "nobody@university.ac.uk",
            "password": "password123",
        }, follow_redirects=True)
        assert b"Invalid email or password" in resp.data

    def test_authenticated_user_redirected_from_login(self, auth_client):
        """An already-logged-in user visiting /auth/login should be redirected."""
        resp = auth_client.get("/auth/login", follow_redirects=False)
        assert resp.status_code == 302

    def test_authenticated_user_redirected_from_register(self, auth_client):
        """An already-logged-in user visiting /auth/register should be redirected."""
        resp = auth_client.get("/auth/register", follow_redirects=False)
        assert resp.status_code == 302

    def test_login_rejects_open_redirect(self, client, sample_user):
        """The ?next= parameter should reject absolute URLs (open redirect attack)."""
        resp = client.post("/auth/login?next=http://evil.com", data={
            "email": "test@university.ac.uk",
            "password": "password123",
        }, follow_redirects=False)
        # Should redirect to index (/) not to evil.com
        assert "evil.com" not in resp.headers.get("Location", "")


class TestLogout:

    def test_logout_redirects(self, auth_client):
        """Logging out should redirect to index."""
        resp = auth_client.get("/auth/logout", follow_redirects=False)
        assert resp.status_code == 302

    def test_logout_message(self, auth_client):
        """Logging out should flash a confirmation message."""
        resp = auth_client.get("/auth/logout", follow_redirects=True)
        assert b"logged out" in resp.data
