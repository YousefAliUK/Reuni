from datetime import datetime, timezone, timedelta
from unittest.mock import patch
import pytest
from app.models import Item, User, CancellationRecord
from app.utils.cancellation import calculate_hours_held, get_cancellation_tier


class TestCancellationTiers:

    def _claim_item(self, db_session, item, buyer):
        """Helper to set up a claim state on an item."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        item.buyer_id = buyer.id
        item.pin_code = "1234"
        item.claimed_at = now
        item.pin_expires_at = now + timedelta(hours=72)
        item.pin_attempts = 0
        db_session.session.commit()

    def test_cancel_within_24h_buyer(self, second_auth_client, sample_item, second_user, db_session):
        """Buyer cancels within 24h: tier is 'clean', record created, item available."""
        self._claim_item(db_session, sample_item, second_user)

        resp = second_auth_client.post(f"/items/{sample_item.id}/cancel-claim", follow_redirects=True)
        assert resp.status_code == 200
        assert b"You cancelled this claim. The item has been returned to the marketplace." in resp.data

        # Verify item is available again
        item = db_session.session.get(Item, sample_item.id)
        assert item.buyer_id is None
        assert item.pin_code is None

        # Verify record exists
        record = CancellationRecord.query.filter_by(item_id=sample_item.id).first()
        assert record is not None
        assert record.tier == "clean"
        assert record.cancelled_by_role == "buyer"
        assert record.cancelled_by_id == second_user.id
        assert record.hours_held < 24.0

    def test_cancel_after_24h_buyer(self, second_auth_client, sample_item, second_user, db_session):
        """Buyer cancels after 24h: tier is 'late', record created, item available."""
        self._claim_item(db_session, sample_item, second_user)

        # Set claimed_at to 25 hours ago
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=25)
        sample_item.claimed_at = past
        db_session.session.commit()

        resp = second_auth_client.post(f"/items/{sample_item.id}/cancel-claim", follow_redirects=True)
        assert resp.status_code == 200
        assert b"You cancelled this claim after 24 hours. This has been recorded" in resp.data

        # Verify record exists
        record = CancellationRecord.query.filter_by(item_id=sample_item.id).first()
        assert record is not None
        assert record.tier == "late"
        assert record.cancelled_by_role == "buyer"
        assert 24.5 < record.hours_held < 25.5

    def test_cancel_within_24h_seller(self, auth_client, sample_item, second_user, db_session):
        """Seller rejects claim within 24h: tier is 'clean', role is 'seller'."""
        self._claim_item(db_session, sample_item, second_user)

        resp = auth_client.post(f"/items/{sample_item.id}/cancel-claim", follow_redirects=True)
        assert resp.status_code == 200
        assert b"You cancelled this claim. The item has been returned to the marketplace." in resp.data

        # Verify record exists
        record = CancellationRecord.query.filter_by(item_id=sample_item.id).first()
        assert record is not None
        assert record.tier == "clean"
        assert record.cancelled_by_role == "seller"
        assert record.cancelled_by_id == sample_item.seller_id

    def test_cancel_after_24h_seller(self, auth_client, sample_item, second_user, db_session):
        """Seller rejects claim after 24h: tier is 'late', role is 'seller'."""
        self._claim_item(db_session, sample_item, second_user)

        # Set claimed_at to 40 hours ago
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=40)
        sample_item.claimed_at = past
        db_session.session.commit()

        resp = auth_client.post(f"/items/{sample_item.id}/cancel-claim", follow_redirects=True)
        assert resp.status_code == 200
        assert b"You cancelled this claim after 24 hours." in resp.data

        # Verify record exists
        record = CancellationRecord.query.filter_by(item_id=sample_item.id).first()
        assert record is not None
        assert record.tier == "late"
        assert record.cancelled_by_role == "seller"
        assert 39.5 < record.hours_held < 40.5

    def test_unauthorized_cancellation_403(self, client, sample_item, second_user, db_session):
        """Third party cannot cancel someone else's claim (should return 403)."""
        self._claim_item(db_session, sample_item, second_user)

        # Anonymous request
        resp = client.post(f"/items/{sample_item.id}/cancel-claim")
        # Flask-Login redirects anonymous users to login page (302)
        assert resp.status_code == 302

        # Create a third user and log them in
        third_user = User(
            email="third@university.ac.uk",
            name="Third User",
            phone_number="+447700100009",
            is_verified=True,
            university_domain="university.ac.uk",
        )
        third_user.set_password("StrongPass123")
        db_session.session.add(third_user)
        db_session.session.commit()

        third_client = client
        third_client.post("/auth/login", data={
            "email": "third@university.ac.uk",
            "password": "StrongPass123",
        }, follow_redirects=True)

        # Third user tries to cancel
        resp2 = third_client.post(f"/items/{sample_item.id}/cancel-claim")
        assert resp2.status_code == 403

    def test_cannot_cancel_already_completed(self, second_auth_client, sample_item, second_user, db_session):
        """Cannot cancel an already completed/sold transaction."""
        self._claim_item(db_session, sample_item, second_user)
        sample_item.is_sold = True
        db_session.session.commit()

        resp = second_auth_client.post(f"/items/{sample_item.id}/cancel-claim", follow_redirects=True)
        assert b"This exchange is already complete" in resp.data

        # No record should be created
        records = CancellationRecord.query.filter_by(item_id=sample_item.id).all()
        assert len(records) == 0

    def test_cannot_cancel_unclaimed_item(self, second_auth_client, sample_item, db_session):
        """Cannot cancel an item that is not claimed."""
        assert sample_item.buyer_id is None

        resp = second_auth_client.post(f"/items/{sample_item.id}/cancel-claim", follow_redirects=True)
        assert b"This item is no longer claimed" in resp.data

        # No record should be created
        records = CancellationRecord.query.filter_by(item_id=sample_item.id).all()
        assert len(records) == 0

    def test_auto_expired_cancellation_prevention(self, second_auth_client, sample_item, second_user, db_session):
        """Manual cancellation of an already auto-expired claim fails gracefully (shows expired, no record)."""
        self._claim_item(db_session, sample_item, second_user)

        # Set claimed_at to 73 hours ago (expired)
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=73)
        sample_item.claimed_at = past
        db_session.session.commit()

        resp = second_auth_client.post(f"/items/{sample_item.id}/cancel-claim", follow_redirects=True)
        assert b"This claim already expired automatically" in resp.data

        # Item should be released from claim (due to cleanup in route)
        item = db_session.session.get(Item, sample_item.id)
        assert item.buyer_id is None

        # No CancellationRecord should be created
        records = CancellationRecord.query.filter_by(item_id=sample_item.id).all()
        assert len(records) == 0

    def test_email_notification_sent_on_cancellation(self, second_auth_client, sample_item, sample_user, second_user, db_session):
        """Email notification sent with correct subject and body contents to other party."""
        self._claim_item(db_session, sample_item, second_user)

        from app.utils.emails import outbox
        resp = second_auth_client.post(f"/items/{sample_item.id}/cancel-claim", follow_redirects=True)
        assert resp.status_code == 200
        
        # Assert email sent to seller (since buyer cancelled)
        assert len(outbox) == 1
        email_msg = outbox[0]
        assert email_msg.subject == f"A claim on {sample_item.title} has been cancelled"
        assert sample_user.email in email_msg.recipients
        assert "Cancelled by" in email_msg.html_content
        assert "buyer" in email_msg.html_content
        assert "Item name" in email_msg.html_content
        assert sample_item.title in email_msg.html_content
        assert "Other User cancelled their claim on" in email_msg.html_content
        assert f"/items/{sample_item.id}" in email_msg.html_content

    def test_email_failure_resiliency(self, second_auth_client, sample_item, second_user, db_session):
        """Email sending failure does not abort or roll back the cancellation transaction."""
        self._claim_item(db_session, sample_item, second_user)

        # Mock send_email to raise an exception
        with patch("app.routes.items.send_email", side_effect=Exception("API Down")):
            resp = second_auth_client.post(f"/items/{sample_item.id}/cancel-claim", follow_redirects=True)
            # The request should still complete successfully
            assert resp.status_code == 200
            assert b"You cancelled this claim" in resp.data

        # The item should still be cancelled in DB
        item = db_session.session.get(Item, sample_item.id)
        assert item.buyer_id is None

        # The record should still exist
        record = CancellationRecord.query.filter_by(item_id=sample_item.id).first()
        assert record is not None

    def test_timezone_robustness(self):
        """Utility handles naive and timezone-aware datetimes correctly."""
        now_utc = datetime.now(timezone.utc)
        now_naive = now_utc.replace(tzinfo=None)

        # Test calculate_hours_held with naive input
        hours_naive = calculate_hours_held(now_naive)
        assert hours_naive >= 0.0

        # Test calculate_hours_held with aware input
        hours_aware = calculate_hours_held(now_utc)
        assert hours_aware >= 0.0

    def test_get_cancellation_tier_boundary(self):
        """Boundary checks for tier categorization (exactly 24h, 23.9h, 24.1h)."""
        now = datetime.now(timezone.utc)

        # 23.9 hours ago should be clean
        claimed_23_9 = now - timedelta(hours=23, minutes=54)
        assert get_cancellation_tier(claimed_23_9) == "clean"

        # Exactly 24.0 hours ago should be clean
        claimed_24 = now - timedelta(hours=24)
        assert get_cancellation_tier(claimed_24) == "clean"

        # 24.1 hours ago should be late
        claimed_24_1 = now - timedelta(hours=24, minutes=6)
        assert get_cancellation_tier(claimed_24_1) == "late"
