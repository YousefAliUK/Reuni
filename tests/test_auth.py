"""
Reuni — Auth Route Tests
Covers registration, login, logout, and edge cases.
"""

from app.models import User
from unittest.mock import patch


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
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
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
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        }, follow_redirects=True)
        assert b"already exists" in resp.data

    def test_register_password_mismatch(self, client):
        """Mismatched passwords should flash an error."""
        resp = client.post("/auth/register", data={
            "email": "mismatch@university.ac.uk",
            "name": "Mismatch",
            "phone_number": "07912345678",
            "password": "StrongPass123",
            "confirm_password": "DifferentPass123",
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
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        }, follow_redirects=True)
        assert b"All fields are required" in resp.data

    def test_duplicate_phone_rejected(self, client, sample_user):
        """Registering with an already used phone number should be rejected."""
        resp = client.post("/auth/register", data={
            "email": "another-email@university.ac.uk",
            "name": "Another User",
            "phone_number": sample_user.phone_number,  # duplicate phone
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        }, follow_redirects=True)
        assert b"already exists" in resp.data

    def test_register_normalises_phone(self, client, db_session):
        """Phone starting with +44 should be stored unchanged."""
        resp = client.post("/auth/register", data={
            "email": "intl@university.ac.uk",
            "name": "Intl User",
            "phone_number": "+447912345678",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
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
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
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
            "password": "StrongPass123",
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
            "password": "StrongPass123",
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
            "password": "StrongPass123",
        }, follow_redirects=False)
        # Should redirect to index (/) not to evil.com
        assert "evil.com" not in resp.headers.get("Location", "")


class TestLogout:

    def test_logout_redirects(self, auth_client):
        """Logging out should redirect to index."""
        resp = auth_client.post("/auth/logout", follow_redirects=False)
        assert resp.status_code == 302

    def test_logout_message(self, auth_client):
        """Logging out should flash a confirmation message."""
        resp = auth_client.post("/auth/logout", follow_redirects=True)
        assert b"logged out" in resp.data


class TestEmailVerification:

    @patch("app.routes.auth.send_otp_email")
    def test_register_creates_unverified_and_sends_email(self, mock_send, client, db_session):
        """Registration with valid Brookes email creates unverified user and sends email."""
        resp = client.post("/auth/register", data={
            "email": "new@brookes.ac.uk",
            "name": "Brookes User",
            "phone_number": "07912345678",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/auth/verify-email")

        user = User.query.filter_by(email="new@brookes.ac.uk").first()
        assert user is not None
        assert user.is_verified is False
        assert user.university_domain == "brookes.ac.uk"
        assert user.email_verification_code is not None
        mock_send.assert_called_once()

    def test_register_invalid_tld_rejected(self, client):
        """Registration with non-.ac.uk email is rejected."""
        resp = client.post("/auth/register", data={
            "email": "student@gmail.com",
            "name": "Invalid TLD",
            "phone_number": "07912345678",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        }, follow_redirects=True)
        assert b"Please use a valid university email address" in resp.data

    def test_register_domain_not_allowed_rejected(self, client):
        """Registration with .ac.uk email not in allowed set is rejected."""
        resp = client.post("/auth/register", data={
            "email": "student@oxford.ac.uk",
            "name": "Not Allowed University",
            "phone_number": "07912345678",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        }, follow_redirects=True)
        assert b"Reuni is not yet available at your university" in resp.data

    @patch("app.routes.auth.send_otp_email")
    def test_re_registration_unverified_overwrites(self, mock_send, client, db_session):
        """Re-registration with same unverified email deletes old record and creates new one."""
        # Create unverified user
        user1 = User(
            email="unverified@brookes.ac.uk",
            name="Unverified One",
            phone_number="+447912345678",
            is_verified=False
        )
        user1.set_password("StrongPass123")
        db_session.session.add(user1)
        db_session.session.commit()

        # Re-register
        resp = client.post("/auth/register", data={
            "email": "unverified@brookes.ac.uk",
            "name": "Unverified Two",
            "phone_number": "07912345678",
            "password": "NewPassword123",
            "confirm_password": "NewPassword123",
        }, follow_redirects=False)
        assert resp.status_code == 302

        # Old user should be deleted, new one created
        users = User.query.filter_by(email="unverified@brookes.ac.uk").all()
        assert len(users) == 1
        assert users[0].name == "Unverified Two"
        assert users[0].check_password("NewPassword123") is True

    @patch("app.routes.auth.send_otp_email")
    def test_re_registration_verified_fails(self, mock_send, client, db_session):
        """Re-registration with same verified email is rejected."""
        user = User(
            email="verified@brookes.ac.uk",
            name="Verified User",
            phone_number="+447912345678",
            is_verified=True
        )
        user.set_password("StrongPass123")
        db_session.session.add(user)
        db_session.session.commit()

        resp = client.post("/auth/register", data={
            "email": "verified@brookes.ac.uk",
            "name": "Verified Re-register",
            "phone_number": "07912345678",
            "password": "NewPassword123",
            "confirm_password": "NewPassword123",
        }, follow_redirects=True)
        assert b"already exists" in resp.data

    @patch("app.routes.auth.send_otp_email")
    def test_verify_valid_code(self, mock_send, client, db_session):
        """Entering valid code verifies the user."""
        # 1. Register to get code generated
        client.post("/auth/register", data={
            "email": "verifytest@brookes.ac.uk",
            "name": "Verify Test",
            "phone_number": "07912345678",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        })

        user = User.query.filter_by(email="verifytest@brookes.ac.uk").first()
        assert user.is_verified is False

        # Retrieve the generated OTP code from mock send call
        args, kwargs = mock_send.call_args
        otp_code = args[2]

        with client.session_transaction() as sess:
            sess["verify_email"] = "verifytest@brookes.ac.uk"

        resp = client.post("/auth/verify-email", data={"code": otp_code}, follow_redirects=True)
        assert b"Email verified" in resp.data

        # Refresh from DB
        db_session.session.refresh(user)
        assert user.is_verified is True
        assert user.email_verification_code is None

    @patch("app.routes.auth.send_otp_email")
    def test_verify_expired_code(self, mock_send, client, db_session):
        """Entering expired code shows error and redirects to resend page."""
        from datetime import datetime, timezone, timedelta
        client.post("/auth/register", data={
            "email": "verifytest@brookes.ac.uk",
            "name": "Verify Test",
            "phone_number": "07912345678",
            "password": "StrongPass123",
            "confirm_password": "StrongPass123",
        })
        user = User.query.filter_by(email="verifytest@brookes.ac.uk").first()
        user.email_verification_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
        db_session.session.commit()

        args, _ = mock_send.call_args
        otp_code = args[2]

        with client.session_transaction() as sess:
            sess["verify_email"] = "verifytest@brookes.ac.uk"

        resp = client.post("/auth/verify-email", data={"code": otp_code}, follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/auth/resend-verification")

    def test_verify_already_verified(self, client, db_session):
        """Entering code when already verified shows 'already verified' message."""
        user = User(
            email="already@brookes.ac.uk",
            name="Already Verified",
            phone_number="+447912345678",
            is_verified=True
        )
        user.set_password("StrongPass123")
        db_session.session.add(user)
        db_session.session.commit()

        with client.session_transaction() as sess:
            sess["verify_email"] = "already@brookes.ac.uk"

        resp = client.post("/auth/verify-email", data={"code": "123456"}, follow_redirects=True)
        assert b"already verified" in resp.data

    def test_login_unverified_rejected(self, client, db_session):
        """Login with unverified account is rejected regardless of correct password."""
        user = User(
            email="unverified@brookes.ac.uk",
            name="Unverified Login",
            phone_number="+447912345678",
            is_verified=False
        )
        user.set_password("StrongPass123")
        db_session.session.add(user)
        db_session.session.commit()

        resp = client.post("/auth/login", data={
            "email": "unverified@brookes.ac.uk",
            "password": "StrongPass123",
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/auth/resend-verification")

    def test_login_verified_succeeds(self, client, db_session):
        """Login with verified account succeeds."""
        user = User(
            email="verified@brookes.ac.uk",
            name="Verified Login",
            phone_number="+447912345678",
            is_verified=True
        )
        user.set_password("StrongPass123")
        db_session.session.add(user)
        db_session.session.commit()

        resp = client.post("/auth/login", data={
            "email": "verified@brookes.ac.uk",
            "password": "StrongPass123",
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert not resp.headers["Location"].endswith("/auth/resend-verification")

    @patch("app.routes.auth.send_otp_email")
    def test_resend_sends_email_for_unverified(self, mock_send, client, db_session):
        """Resend endpoint sends email for unverified account."""
        user = User(
            email="unverified@brookes.ac.uk",
            name="Unverified Resend",
            phone_number="+447912345678",
            is_verified=False
        )
        user.set_password("StrongPass123")
        db_session.session.add(user)
        db_session.session.commit()

        resp = client.post("/auth/resend-verification", data={
            "email": "unverified@brookes.ac.uk"
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/auth/verify-email")
        mock_send.assert_called_once()

    @patch("app.routes.auth.send_otp_email")
    def test_resend_silently_succeeds_for_nonexistent(self, mock_send, client):
        """Resend endpoint silently succeeds for non-existent email (no error revealed)."""
        resp = client.post("/auth/resend-verification", data={
            "email": "nonexistent@brookes.ac.uk"
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/auth/verify-email")
        mock_send.assert_not_called()

    def test_verified_required_decorator(self, client, db_session):
        """verified_required decorator blocks unverified users from protected routes."""
        user = User(
            email="unverified@brookes.ac.uk",
            name="Unverified User",
            phone_number="+447912345678",
            is_verified=False
        )
        user.set_password("StrongPass123")
        db_session.session.add(user)
        db_session.session.commit()

        with client.session_transaction() as sess:
            sess["_user_id"] = str(user.id)

        resp = client.get("/items/new", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/auth/resend-verification")


class TestLockoutAndComplexity:

    def test_account_lockout_login(self, client, db_session):
        """Five failed login attempts should lock the account for 15 minutes."""
        from datetime import datetime, timezone, timedelta
        user = User(
            email="lockout@university.ac.uk",
            name="Lockout User",
            phone_number="+447700100015",
            is_verified=True,
            university_domain="university.ac.uk",
        )
        user.set_password("CorrectPassword123")
        db_session.session.add(user)
        db_session.session.commit()

        # Fail 5 times
        for i in range(5):
            resp = client.post("/auth/login", data={
                "email": "lockout@university.ac.uk",
                "password": "WrongPassword123"
            }, follow_redirects=True)
            if i < 4:
                assert b"Invalid email or password" in resp.data
            else:
                assert b"locked" in resp.data or b"Too many failed login attempts" in resp.data

        # 6th attempt should block with lockout warning
        resp_lockout = client.post("/auth/login", data={
            "email": "lockout@university.ac.uk",
            "password": "CorrectPassword123"
        }, follow_redirects=True)
        assert b"locked due to too many failed login attempts" in resp_lockout.data

        # Fast forward locked_until to past to simulate lockout expiration
        user_db = db_session.session.get(User, user.id)
        user_db.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=1)
        db_session.session.commit()

        # Should now log in successfully and reset failed count & locked_until
        resp_success = client.post("/auth/login", data={
            "email": "lockout@university.ac.uk",
            "password": "CorrectPassword123"
        }, follow_redirects=True)
        assert b"Welcome back" in resp_success.data

        user_after = db_session.session.get(User, user.id)
        assert user_after.failed_login_attempts == 0
        assert user_after.locked_until is None

    def test_password_complexity_registration(self, client):
        """Registration should reject passwords that do not meet complexity requirements."""
        # No digit
        resp1 = client.post("/auth/register", data={
            "email": "complex1@brookes.ac.uk",
            "name": "User One",
            "phone_number": "07900100021",
            "password": "NoDigitsPassword",
            "confirm_password": "NoDigitsPassword"
        }, follow_redirects=True)
        assert b"at least one uppercase letter, one lowercase letter, and one digit" in resp1.data

        # No uppercase
        resp2 = client.post("/auth/register", data={
            "email": "complex2@brookes.ac.uk",
            "name": "User Two",
            "phone_number": "07900100022",
            "password": "nouppercasepassword1",
            "confirm_password": "nouppercasepassword1"
        }, follow_redirects=True)
        assert b"at least one uppercase letter, one lowercase letter, and one digit" in resp2.data

        # Too short
        resp3 = client.post("/auth/register", data={
            "email": "complex3@brookes.ac.uk",
            "name": "User Three",
            "phone_number": "07900100023",
            "password": "Sh1",
            "confirm_password": "Sh1"
        }, follow_redirects=True)
        assert b"must be at least 8 characters long" in resp3.data


class TestPasswordResetTokenUtils:

    def test_generate_and_verify_token_success(self, app):
        from app.utils.tokens import generate_password_reset_token, verify_password_reset_token
        with app.app_context():
            token = generate_password_reset_token("user@university.ac.uk", "hash123", "secret")
            email = verify_password_reset_token(token, "hash123", "secret")
            assert email == "user@university.ac.uk"

    def test_verify_token_expired(self, app):
        from app.utils.tokens import generate_password_reset_token, verify_password_reset_token
        with app.app_context():
            token = generate_password_reset_token("user@university.ac.uk", "hash123", "secret")
            email = verify_password_reset_token(token, "hash123", "secret", max_age_seconds=-1)
            assert email is None

    def test_verify_token_tampered(self, app):
        from app.utils.tokens import generate_password_reset_token, verify_password_reset_token
        with app.app_context():
            token = generate_password_reset_token("user@university.ac.uk", "hash123", "secret")
            tampered_token = token + "extra"
            email = verify_password_reset_token(tampered_token, "hash123", "secret")
            assert email is None

    def test_verify_token_wrong_hash(self, app):
        from app.utils.tokens import generate_password_reset_token, verify_password_reset_token
        with app.app_context():
            token = generate_password_reset_token("user@university.ac.uk", "hash123", "secret")
            email = verify_password_reset_token(token, "different_hash", "secret")
            assert email is None


class TestForgotPassword:

    def test_forgot_password_page_loads(self, client):
        """GET /auth/forgot-password should return 200."""
        resp = client.get("/auth/forgot-password")
        assert resp.status_code == 200
        assert b"Reset your password" in resp.data

    @patch("app.routes.auth.mail.send")
    def test_forgot_password_success(self, mock_send, client, sample_user):
        """POST /auth/forgot-password with valid email sends reset link."""
        resp = client.post("/auth/forgot-password", data={
            "email": "test@university.ac.uk"
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"If an account exists with that email, a reset link has been sent" in resp.data
        mock_send.assert_called_once()
        msg = mock_send.call_args[0][0]
        assert msg.subject == "Password reset for your Reuni account"
        assert "test@university.ac.uk" in msg.recipients
        assert "/auth/reset-password/" in msg.body

    @patch("app.routes.auth.mail.send")
    def test_forgot_password_unregistered_email(self, mock_send, client):
        """POST /auth/forgot-password with unregistered email flashes neutral message and does not send email."""
        resp = client.post("/auth/forgot-password", data={
            "email": "unregistered@university.ac.uk"
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"If an account exists with that email, a reset link has been sent" in resp.data
        mock_send.assert_not_called()

    @patch("app.routes.auth.mail.send")
    def test_forgot_password_unverified_email(self, mock_send, client, db_session):
        """POST /auth/forgot-password with unverified email flashes neutral message and does not send email."""
        unverified_user = User(
            email="unverified@university.ac.uk",
            name="Unverified User",
            phone_number="+447700100012",
            is_verified=False
        )
        unverified_user.set_password("StrongPass123")
        db_session.session.add(unverified_user)
        db_session.session.commit()

        resp = client.post("/auth/forgot-password", data={
            "email": "unverified@university.ac.uk"
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b"If an account exists with that email, a reset link has been sent" in resp.data
        mock_send.assert_not_called()

    def test_forgot_password_rate_limiting(self):
        """Rate limit should reject the 4th request in an hour."""
        from app import create_app, limiter
        from app.config import TestingConfig
        class RateLimitConfig(TestingConfig):
            RATELIMIT_ENABLED = True
        
        limit_app = create_app(RateLimitConfig)
        limit_app.config['WTF_CSRF_ENABLED'] = False
        client = limit_app.test_client()
        
        try:
            for _ in range(3):
                resp = client.post("/auth/forgot-password", data={"email": "ratelimit@university.ac.uk"})
                assert resp.status_code == 302
            resp = client.post("/auth/forgot-password", data={"email": "ratelimit@university.ac.uk"})
            assert resp.status_code == 429
        finally:
            limiter.enabled = False

    def test_authenticated_user_forgot_password_redirect(self, auth_client):
        """Logged-in user should be redirected to index."""
        resp = auth_client.get("/auth/forgot-password", follow_redirects=False)
        assert resp.status_code == 302
        assert resp.headers["Location"].endswith("/")


class TestResetPassword:

    def test_reset_password_page_loads(self, client, sample_user):
        """GET /auth/reset-password/<token> with valid token should render form."""
        from app.utils.tokens import generate_password_reset_token
        from flask import current_app
        with client.application.app_context():
            token = generate_password_reset_token(
                sample_user.email, sample_user.password_hash, current_app.config["SECRET_KEY"]
            )
        
        resp = client.get(f"/auth/reset-password/{token}")
        assert resp.status_code == 200
        assert b"Set a new password" in resp.data

    def test_reset_password_expired_token(self, client, sample_user):
        """Expired token should redirect to forgot-password with error."""
        from app.utils.tokens import generate_password_reset_token
        from flask import current_app
        with client.application.app_context():
            token = generate_password_reset_token(
                sample_user.email, sample_user.password_hash, current_app.config["SECRET_KEY"]
            )
        with patch("app.routes.auth.verify_password_reset_token", return_value=None):
            resp = client.get(f"/auth/reset-password/{token}", follow_redirects=True)
            assert b"This reset link is invalid or has expired." in resp.data
            assert b"Reset your password" in resp.data

    def test_reset_password_tampered_token(self, client):
        """Tampered token should redirect to forgot-password with error."""
        resp = client.get("/auth/reset-password/garbage_token", follow_redirects=True)
        assert b"This reset link is invalid." in resp.data
        assert b"Reset your password" in resp.data

    def test_reset_password_success(self, client, sample_user, db_session):
        """POST /auth/reset-password/<token> with valid data updates password in DB."""
        from app.utils.tokens import generate_password_reset_token
        from flask import current_app
        
        old_hash = sample_user.password_hash

        with client.application.app_context():
            token = generate_password_reset_token(
                sample_user.email, sample_user.password_hash, current_app.config["SECRET_KEY"]
            )

        resp = client.post(f"/auth/reset-password/{token}", data={
            "new_password": "NewStrongPass123",
            "confirm_password": "NewStrongPass123"
        }, follow_redirects=True)

        assert b"Password updated. You can now log in." in resp.data
        
        db_session.session.refresh(sample_user)
        assert sample_user.password_hash != old_hash
        assert sample_user.check_password("NewStrongPass123") is True
        
        resp_reuse = client.get(f"/auth/reset-password/{token}", follow_redirects=True)
        assert b"This reset link is invalid or has expired" in resp_reuse.data

    def test_reset_password_mismatch(self, client, sample_user):
        """POST /auth/reset-password/<token> with mismatched passwords re-renders form with error."""
        from app.utils.tokens import generate_password_reset_token
        from flask import current_app
        with client.application.app_context():
            token = generate_password_reset_token(
                sample_user.email, sample_user.password_hash, current_app.config["SECRET_KEY"]
            )

        resp = client.post(f"/auth/reset-password/{token}", data={
            "new_password": "NewStrongPass123",
            "confirm_password": "MismatchedPass123"
        }, follow_redirects=True)
        assert b"Passwords do not match" in resp.data
        assert b"Set a new password" in resp.data

    def test_reset_password_same_as_current(self, client, sample_user):
        """POST /auth/reset-password/<token> with same password flashes error."""
        from app.utils.tokens import generate_password_reset_token
        from flask import current_app
        with client.application.app_context():
            token = generate_password_reset_token(
                sample_user.email, sample_user.password_hash, current_app.config["SECRET_KEY"]
            )

        resp = client.post(f"/auth/reset-password/{token}", data={
            "new_password": "StrongPass123",
            "confirm_password": "StrongPass123"
        }, follow_redirects=True)
        assert b"must be different from your current password" in resp.data

    def test_reset_password_complexity(self, client, sample_user):
        """POST /auth/reset-password/<token> with password failing complexity rules flashes error."""
        from app.utils.tokens import generate_password_reset_token
        from flask import current_app
        with client.application.app_context():
            token = generate_password_reset_token(
                sample_user.email, sample_user.password_hash, current_app.config["SECRET_KEY"]
            )

        resp1 = client.post(f"/auth/reset-password/{token}", data={
            "new_password": "Sh1",
            "confirm_password": "Sh1"
        }, follow_redirects=True)
        assert b"must be at least 8 characters long" in resp1.data

        resp2 = client.post(f"/auth/reset-password/{token}", data={
            "new_password": "NoDigitsPassword",
            "confirm_password": "NoDigitsPassword"
        }, follow_redirects=True)
        assert b"must contain at least one uppercase letter, one lowercase letter, and one digit" in resp2.data


