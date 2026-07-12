import os
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from app.models import User, Item, CancellationRecord
from tests.conftest import make_test_image


class TestGDPRDeletion:

    def test_delete_requires_confirmation_text(self, auth_client, sample_user, db_session):
        """POST /settings/delete with incorrect confirm text should abort."""
        resp = auth_client.post(
            "/settings/delete",
            data={"delete_confirm_text": "NOTDELETE"},
            follow_redirects=True
        )
        assert b"Confirmation text did not match" in resp.data
        
        # Verify user is still active and email is intact
        user = db_session.session.get(User, sample_user.id)
        assert user.is_active is True
        assert user.email == "test@university.ac.uk"

    def test_role_guards_admin_cannot_delete(self, client, db_session):
        """Admin role cannot be deleted via settings route."""
        admin = User(
            email="admin@university.ac.uk",
            name="Admin User",
            is_verified=True,
            role="admin",
            university_domain="university.ac.uk"
        )
        admin.set_password("StrongPass123")
        db_session.session.add(admin)
        db_session.session.commit()

        # Log in admin
        client.post("/auth/login", data={"email": "admin@university.ac.uk", "password": "StrongPass123"})
        
        resp = client.post(
            "/settings/delete",
            data={"delete_confirm_text": "DELETE"},
            follow_redirects=True
        )
        assert b"Administrator accounts cannot be deleted directly" in resp.data
        
        # Verify admin is active
        u = db_session.session.get(User, admin.id)
        assert u.is_active is True

    def test_role_guards_partner_cannot_delete(self, client, db_session):
        """Partner role cannot be deleted via settings route."""
        partner = User(
            email="partner@university.ac.uk",
            name="Partner User",
            is_verified=True,
            role="partner",
            university_domain="university.ac.uk"
        )
        partner.set_password("StrongPass123")
        db_session.session.add(partner)
        db_session.session.commit()

        # Log in partner
        client.post("/auth/login", data={"email": "partner@university.ac.uk", "password": "StrongPass123"})
        
        resp = client.post(
            "/settings/delete",
            data={"delete_confirm_text": "DELETE"},
            follow_redirects=True
        )
        assert b"Partner accounts cannot be deleted directly" in resp.data
        
        # Verify partner is active
        u = db_session.session.get(User, partner.id)
        assert u.is_active is True

    def test_delete_success_deactivates_and_queues(self, auth_client, sample_user, db_session):
        """Successful deletion deactivates user and sets deletion_pending_until."""
        resp = auth_client.post(
            "/settings/delete",
            data={"delete_confirm_text": "DELETE"},
            follow_redirects=True
        )
        assert b"Your account has been deactivated and is scheduled for permanent deletion" in resp.data

        # Verify user is deactivated but email/phone are still kept for the 30-day block
        user = db_session.session.get(User, sample_user.id)
        assert user.is_active is False
        assert user.deletion_pending_until is not None
        assert user.email == "test@university.ac.uk"
        
        # Confirm lockout
        resp_login = auth_client.post(
            "/auth/login",
            data={"email": "test@university.ac.uk", "password": "StrongPass123"},
            follow_redirects=True
        )
        assert b"Invalid email or password" in resp_login.data

    def test_idempotency_guard_double_delete(self, auth_client, sample_user, db_session):
        """Submitting deletion request twice redirects safely without database constraints errors."""
        resp1 = auth_client.post(
            "/settings/delete",
            data={"delete_confirm_text": "DELETE"},
            follow_redirects=True
        )
        assert b"Your account has been deactivated" in resp1.data

        # Attempt to post again to the delete route (which shouldn't break DB unique constraints)
        resp2 = auth_client.post(
            "/settings/delete",
            data={"delete_confirm_text": "DELETE"},
            follow_redirects=True
        )
        # Should redirect to index or home without throwing a 500 error
        assert resp2.status_code == 200

    def test_cancels_claims_with_notifications(self, app, client, sample_user, second_user, sample_item, db_session):
        """Account deletion cancels pending claims and notifies the other party."""
        # Setup a pending claim: second_user claims sample_user's item
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = "1234"
        sample_item.claimed_at = now
        sample_item.pin_expires_at = now + timedelta(hours=72)
        db_session.session.commit()

        # Log in as buyer (second_user)
        client.post("/auth/login", data={"email": "other@university.ac.uk", "password": "StrongPass123"})

        from app.utils.emails import outbox
        resp = client.post(
            "/settings/delete",
            data={"delete_confirm_text": "DELETE"},
            follow_redirects=True
        )
        assert resp.status_code == 200

        # Claim should be cancelled, item remains since seller is active
        item = db_session.session.get(Item, sample_item.id)
        assert item is not None
        assert item.buyer_id is None
        assert item.pin_code is None

        # Email notification sent to the seller (sample_user)
        assert len(outbox) == 1
        email_msg = outbox[0]
        assert email_msg.subject == f"A claim on {sample_item.title} has been cancelled"
        assert sample_user.email in email_msg.recipients
        assert "deactivated for deletion" in email_msg.html_content

    def test_removes_active_listings_and_images(self, auth_client, sample_user, sample_item, db_session, app):
        """Unsold listings of the user are hard-deleted, and their image files are removed from disk."""
        # Create a mock image file on disk matching sample_item's image_filename
        image_name = sample_item.image_filename
        uploads_dir = os.path.join(app.static_folder, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        img_path = os.path.join(uploads_dir, image_name)
        with open(img_path, "w") as f:
            f.write("mock_image_data")

        assert os.path.isfile(img_path) is True

        resp = auth_client.post(
            "/settings/delete",
            data={"delete_confirm_text": "DELETE"},
            follow_redirects=True
        )
        assert resp.status_code == 200

        # Unsold item row should be soft-deleted
        item = db_session.session.get(Item, sample_item.id)
        assert item.is_deleted is True
        assert item.image_filename is None

        # Image file on disk should be deleted
        assert os.path.isfile(img_path) is False

    def test_keeps_sold_listings_and_cancellations_with_anonymisation(self, app, client, sample_user, second_user, sample_item, db_session):
        """Sold items and cancellation history pointing to the user are kept but referencing anonymised user."""
        # 1. Setup a completed transaction (sold item)
        sold_item = Item(
            title="Sold Textbook",
            description="Sold description",
            category="Books",
            condition="Good",
            price=10.00,
            is_free=False,
            seller_id=sample_user.id,
            buyer_id=second_user.id,
            is_sold=True,
            university_domain=sample_user.university_domain,
        )
        db_session.session.add(sold_item)
        db_session.session.commit()

        # 2. Setup a past Cancellation Record involving the user
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        cancellation = CancellationRecord(
            item_id=sample_item.id,
            cancelled_by_id=sample_user.id,
            other_party_id=second_user.id,
            claimed_at=now - timedelta(hours=5),
            cancelled_at=now,
            hours_held=5.0,
            tier="clean",
            cancelled_by_role="seller"
        )
        db_session.session.add(cancellation)
        db_session.session.commit()

        # Log in and delete
        client.post("/auth/login", data={"email": "test@university.ac.uk", "password": "StrongPass123"})
        
        # Directly anonymise user context for Day 30 JIT check
        with app.app_context():
            u = db_session.session.get(User, sample_user.id)
            u.anonymise()
            db_session.session.commit()

            # Verify anonymisation results
            assert u.name == "Deleted User"
            assert u.email == f"deleted_{sample_user.id}@deleted.reuni"
            assert u.university_domain is None
            assert u.kg_saved_total == 0.0
            assert u.failed_login_attempts == 0
            assert u.locked_until is None

            # Verify sold item still exists in database pointing to user ID
            s_item = db_session.session.get(Item, sold_item.id)
            assert s_item is not None
            assert s_item.seller_id == sample_user.id
            assert s_item.is_sold is True
            # Retaining university_domain for ESG reports
            assert s_item.university_domain == "university.ac.uk"

            # Verify cancellation record still exists
            record = db_session.session.get(CancellationRecord, cancellation.id)
            assert record is not None
            assert record.cancelled_by_id == sample_user.id
            # cancellation_records.other_party_id and cancelled_by_id point to anonymised row
            assert record.cancelled_by.name == "Deleted User"

    def test_jit_cleanup_on_registration_after_cooldown(self, client, sample_user, db_session):
        """A new user can register with the same email once the 30-day deactivation expires, triggering cleanup."""
        # 1. Place sample_user in pending deactivation state
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        sample_user.is_active = False
        # Set expiry date to 1 hour in the past (expired cooldown)
        sample_user.deletion_pending_until = now - timedelta(hours=1)
        db_session.session.commit()

        # 2. Register a new user using the same email address
        resp = client.post(
            "/auth/register",
            data={
                "name": "New Person",
                "email": "test@university.ac.uk",
                "password": "NewStrongPass1",
                "confirm_password": "NewStrongPass1",
            },
            follow_redirects=True
        )
        assert b"verification code" in resp.data

        # 3. Verify that the old account has been fully anonymised
        old_user = User.query.filter_by(name="Deleted User").first()
        assert old_user is not None
        assert old_user.id == sample_user.id
        assert old_user.email == f"deleted_{sample_user.id}@deleted.reuni"

        # 4. Verify that the new user is created and pending verification
        new_user = User.query.filter_by(email="test@university.ac.uk").first()
        assert new_user is not None
        assert new_user.id != sample_user.id
        assert new_user.name == "New Person"
        assert new_user.is_verified is False

    def test_jit_cleanup_on_registration_blocked_during_cooldown(self, client, sample_user, db_session):
        """A new user cannot register with the same email while the 30-day deactivation is still active."""
        # 1. Place sample_user in pending deactivation state
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        sample_user.is_active = False
        # Set expiry date to 29 days in the future (active cooldown)
        sample_user.deletion_pending_until = now + timedelta(days=29)
        db_session.session.commit()

        # 2. Try to register a new user using the same email address
        resp = client.post(
            "/auth/register",
            data={
                "name": "New Person",
                "email": "test@university.ac.uk",
                "password": "NewStrongPass1",
                "confirm_password": "NewStrongPass1",
            },
            follow_redirects=True
        )
        assert b"verification code" in resp.data

        # Old account should remain intact (not anonymised)
        user = db_session.session.get(User, sample_user.id)
        assert user.email == "test@university.ac.uk"
        assert user.name == "Test User"

    def test_cron_anonymisation_job(self, app, db_session, sample_user, second_user):
        """Test the background cron anonymisation job cleans up expired accounts, but leaves others intact."""
        from app.scheduler import anonymise_expired_accounts

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # User 1: expired cooldown (deactivated, deletion_pending_until in the past)
        sample_user.is_active = False
        sample_user.deletion_pending_until = now - timedelta(days=1)
        
        # User 2: active cooldown (deactivated, deletion_pending_until in the future)
        second_user.is_active = False
        second_user.deletion_pending_until = now + timedelta(days=29)
        
        db_session.session.commit()

        # Invoke the job synchronously with the test app instance
        anonymise_expired_accounts(app)

        # Retrieve users from database to inspect
        user1 = db_session.session.get(User, sample_user.id)
        user2 = db_session.session.get(User, second_user.id)

        # Assert User 1 (expired) is fully anonymised
        assert user1.name == "Deleted User"
        assert user1.email == f"deleted_{sample_user.id}@deleted.reuni"
        assert user1.university_domain is None
        assert user1.is_active is False
        assert user1.deletion_pending_until is None

        # Assert User 2 (unexpired) is intact
        assert user2.name == "Other User"
        assert user2.email == "other@university.ac.uk"
        assert user2.university_domain == "university.ac.uk"
        assert user2.is_active is False
        assert user2.deletion_pending_until is not None

    def test_delete_account_rate_limiting(self):
        """Test that POST /settings/delete is rate-limited to 3 requests per hour."""
        from app import create_app, limiter, db
        from app.models import User
        from app.config import TestingConfig

        orig_enabled = limiter.enabled
        orig_app = limiter.app

        class RateLimitConfig(TestingConfig):
            RATELIMIT_ENABLED = True

        limit_app = create_app(RateLimitConfig)
        limit_app.config["WTF_CSRF_ENABLED"] = False
        client = limit_app.test_client()

        with limit_app.app_context():
            user = User(
                email="ratelimit@university.ac.uk",
                name="Rate Limit User",
                is_verified=True,
                university_domain="university.ac.uk",
            )
            user.set_password("StrongPass123")
            db.session.add(user)
            db.session.commit()

        # Log in the user
        client.post(
            "/auth/login",
            data={"email": "ratelimit@university.ac.uk", "password": "StrongPass123"},
            follow_redirects=True
        )

        # Clean up duplicate limits registered on the global limiter due to multiple create_app() calls
        for k in list(limiter.limit_manager._decorated_limits.keys()):
            if "delete_account" in k:
                limits_set = limiter.limit_manager._decorated_limits[k]
                if len(limits_set) > 1:
                    first_limit = next(iter(limits_set))
                    limits_set.clear()
                    limits_set.add(first_limit)

        limiter.enabled = True
        try:
            # 3 requests with wrong confirmation text (rejected by validation, keeping session active)
            for _ in range(3):
                resp = client.post(
                    "/settings/delete",
                    data={"delete_confirm_text": "NOTDELETE"}
                )
                assert resp.status_code in (200, 302)
            
            # 4th request should be rate limited
            resp = client.post(
                "/settings/delete",
                data={"delete_confirm_text": "NOTDELETE"}
            )
            assert resp.status_code == 429
        finally:
            limiter.enabled = orig_enabled
            limiter.app = orig_app

