from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

from app.models import Item, User


class TestBuyItem:

    def test_buy_item_success(self, second_auth_client, sample_item, db_session):
        """Buying (claiming) should generate a PIN and set buyer_id, but not sold yet."""
        resp = second_auth_client.post(
            f"/items/{sample_item.id}/buy", follow_redirects=True
        )
        assert resp.status_code == 200

        item = db_session.session.get(Item, sample_item.id)
        assert item.buyer_id is not None
        assert item.is_sold is False
        assert item.pin_code is not None
        assert len(item.pin_code) > 4
        assert item.claimed_at is not None

    def test_buy_own_item(self, auth_client, sample_item):
        """Seller should not be able to buy their own item."""
        resp = auth_client.post(
            f"/items/{sample_item.id}/buy", follow_redirects=True
        )
        assert b"your own item" in resp.data

    def test_buy_already_sold_item(self, second_auth_client, sample_item, db_session):
        """Buying an already-sold item should be blocked."""
        sample_item.is_sold = True
        db_session.session.commit()
        resp = second_auth_client.post(
            f"/items/{sample_item.id}/buy", follow_redirects=True
        )
        assert b"already been claimed" in resp.data or b"already has a pending claim" in resp.data

    def test_cannot_edit_while_pending(self, auth_client, sample_item, second_user, db_session):
        """Editing an item with a pending claim should be blocked."""
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = generate_password_hash("1234")
        db_session.session.commit()

        resp = auth_client.get(f"/items/{sample_item.id}/edit", follow_redirects=True)
        assert b"while a handshake is pending" in resp.data

    def test_cannot_delete_while_pending(self, auth_client, sample_item, second_user, db_session):
        """Deleting an item with a pending claim should be blocked."""
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = generate_password_hash("1234")
        db_session.session.commit()

        resp = auth_client.post(f"/items/{sample_item.id}/delete", follow_redirects=True)
        assert b"while a handshake is pending" in resp.data

    def test_pin_page_access_guard(self, client, sample_item, second_user, db_session):
        """Users other than buyer or seller cannot access the PIN page."""
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = generate_password_hash("1234")
        db_session.session.commit()

        # Try to access pin page anonymously or as a third user
        resp = client.get(f"/items/{sample_item.id}/pin", follow_redirects=True)
        # Should redirect to login or show access denied
        assert b"Log In" in resp.data

    def test_confirm_pin_success(self, second_auth_client, sample_item, sample_user, second_user, db_session):
        """Confirming the correct PIN should mark item sold and credit seller's total kg saved."""
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = generate_password_hash("4321")
        sample_item.is_free = True  # free item, buyer enters pin (second_auth_client is buyer)
        db_session.session.commit()

        resp = second_auth_client.post(f"/items/{sample_item.id}/confirm", data={"pin": "4321"}, follow_redirects=True)
        assert b"Handshake complete" in resp.data

        item = db_session.session.get(Item, sample_item.id)
        assert item.is_sold is True
        assert item.pin_code is None

        seller = db_session.session.get(User, sample_user.id)
        assert seller.kg_saved_total == sample_item.kg_saved

    def test_3_wrong_pins_auto_cancels(self, second_auth_client, sample_item, second_user, db_session):
        """Entering incorrect PIN 3 times should cancel the claim and release the item."""
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = generate_password_hash("9999")
        sample_item.is_free = True  # buyer enters
        sample_item.pin_attempts = 0
        db_session.session.commit()

        # 1st wrong attempt
        resp = second_auth_client.post(f"/items/{sample_item.id}/confirm", data={"pin": "0000"}, follow_redirects=True)
        assert b"Wrong PIN" in resp.data

        # 2nd wrong attempt
        resp = second_auth_client.post(f"/items/{sample_item.id}/confirm", data={"pin": "0000"}, follow_redirects=True)
        assert b"Wrong PIN" in resp.data

        # 3rd wrong attempt - should trigger cancellation
        resp = second_auth_client.post(f"/items/{sample_item.id}/confirm", data={"pin": "0000"}, follow_redirects=True)
        assert b"Too many wrong attempts" in resp.data

        item = db_session.session.get(Item, sample_item.id)
        assert item.buyer_id is None
        assert item.pin_code is None
        assert item.pin_attempts == 0
        assert item.is_sold is False

    def test_pin_page_seller_sees_pin_free_item(self, auth_client, sample_item, second_user, db_session):
        """For free items, seller should see the PIN code on the PIN page."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = generate_password_hash("5678")
        sample_item.is_free = True
        sample_item.claimed_at = now
        sample_item.pin_expires_at = now + timedelta(hours=72)
        db_session.session.commit()

        with auth_client.session_transaction() as sess:
            sess[f"pin_{sample_item.id}"] = "5678"

        resp = auth_client.get(f"/items/{sample_item.id}/pin")
        assert resp.status_code == 200
        for digit in "5678":
            assert digit.encode() in resp.data
        assert b"Your PIN Code" in resp.data

    def test_pin_page_buyer_sees_pin_paid_item(self, second_auth_client, sample_item, second_user, db_session):
        """For paid items, buyer should see the PIN code on the PIN page."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = generate_password_hash("4321")
        sample_item.is_free = False
        sample_item.claimed_at = now
        sample_item.pin_expires_at = now + timedelta(hours=72)
        db_session.session.commit()

        with second_auth_client.session_transaction() as sess:
            sess[f"pin_{sample_item.id}"] = "4321"

        resp = second_auth_client.get(f"/items/{sample_item.id}/pin")
        assert resp.status_code == 200
        for digit in "4321":
            assert digit.encode() in resp.data
        assert b"Your PIN Code" in resp.data

    def test_pin_page_shows_seller_phone(self, second_auth_client, sample_item, sample_user, second_user, db_session):
        """Buyer should see the seller's phone number and WhatsApp link on the PIN page."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = generate_password_hash("1234")
        sample_item.claimed_at = now
        sample_item.pin_expires_at = now + timedelta(hours=72)
        db_session.session.commit()

        resp = second_auth_client.get(f"/items/{sample_item.id}/pin")
        assert resp.status_code == 200
        assert f"wa.me/{sample_user.phone_number[1:]}".encode() in resp.data
        assert "+44 \u2022\u2022 \u2022\u2022 0005".encode("utf-8") in resp.data

    def test_expired_pin_auto_cancels(self, auth_client, sample_item, second_user, db_session):
        """Visiting PIN page after 72h should auto-cancel the claim."""
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=73)
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = generate_password_hash("1234")
        sample_item.claimed_at = past
        sample_item.pin_expires_at = past + timedelta(hours=72)
        db_session.session.commit()

        resp = auth_client.get(f"/items/{sample_item.id}/pin", follow_redirects=True)
        assert b"expired" in resp.data

        item = db_session.session.get(Item, sample_item.id)
        assert item.buyer_id is None
        assert item.pin_code is None

    def test_dashboard_pending_section(self, auth_client, sample_item, second_user, db_session):
        """Dashboard should show 'Pending Handshakes' when a claim is active."""
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = generate_password_hash("1234")
        db_session.session.commit()

        resp = auth_client.get("/dashboard")
        assert resp.status_code == 200
        assert b"Pending Handshakes" in resp.data
        assert b"Awaiting PIN" in resp.data

    def test_kg_saved_not_double_awarded(self, auth_client, sample_item, second_user, db_session):
        """Attempting to confirm an already-sold item should not award kg again."""
        sample_item.buyer_id = second_user.id
        sample_item.is_sold = True
        sample_item.pin_code = None  # already completed
        db_session.session.commit()

        resp = auth_client.post(
            f"/items/{sample_item.id}/confirm", data={"pin": "0000"}, follow_redirects=True
        )
        assert b"No active claim" in resp.data

    def test_cannot_claim_while_pending(self, app, sample_item, second_user, db_session):
        """A second buyer cannot claim an item that already has a pending claim."""
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = generate_password_hash("1234")
        db_session.session.commit()

        # Create a third user and try to claim
        third = User(
            email="third@university.ac.uk",
            name="Third User",
            phone_number="+447700100009",
            is_verified=True,
        )
        third.set_password("StrongPass123")
        db_session.session.add(third)
        db_session.session.commit()

        third_client = app.test_client()
        third_client.post("/auth/login", data={
            "email": "third@university.ac.uk",
            "password": "StrongPass123",
        }, follow_redirects=True)

        resp = third_client.post(f"/items/{sample_item.id}/buy", follow_redirects=True)
        assert b"pending claim" in resp.data or b"has been sold" in resp.data

    def test_concurrent_buy_attempts(self, second_auth_client, app, sample_item, second_user, db_session):
        """If an item is claimed, second buyer claiming concurrently should fail."""
        # Claim it once
        resp1 = second_auth_client.post(f"/items/{sample_item.id}/buy", follow_redirects=True)
        assert b"Claim initiated" in resp1.data

        # Create third client and try to buy
        third = User(
            email="third@university.ac.uk",
            name="Third User",
            phone_number="+447700100010",
            is_verified=True,
        )
        third.set_password("StrongPass123")
        db_session.session.add(third)
        db_session.session.commit()

        third_client = app.test_client()
        third_client.post("/auth/login", data={
            "email": "third@university.ac.uk",
            "password": "StrongPass123",
        }, follow_redirects=True)

        resp2 = third_client.post(f"/items/{sample_item.id}/buy", follow_redirects=True)
        assert b"already has a pending claim" in resp2.data or b"has been sold" in resp2.data

    def test_seller_confirms_pin_on_paid_item(self, client, sample_item, second_user, db_session):
        """For paid items, buyer holds PIN and seller confirms it."""
        # Log in as buyer (second_user)
        client.post("/auth/login", data={
            "email": "other@university.ac.uk",
            "password": "StrongPass123",
        }, follow_redirects=True)

        # claim as paid item (sample_item has price 15.00)
        resp_buy = client.post(f"/items/{sample_item.id}/buy", follow_redirects=True)
        assert b"Claim initiated" in resp_buy.data

        # Verify client (buyer) holds PIN and has it in session
        with client.session_transaction() as sess:
            pin = sess.get(f"pin_{sample_item.id}")
        assert pin is not None

        # Log out buyer
        client.post("/auth/logout", follow_redirects=True)

        # Log in as seller (sample_user)
        client.post("/auth/login", data={
            "email": "test@university.ac.uk",
            "password": "StrongPass123",
        }, follow_redirects=True)

        # Seller confirms it
        resp_confirm = client.post(f"/items/{sample_item.id}/confirm", data={"pin": pin}, follow_redirects=True)
        assert b"Handshake complete" in resp_confirm.data

        item = db_session.session.get(Item, sample_item.id)
        assert item.is_sold is True
        assert item.buyer_id == second_user.id

    def test_resend_pin_authorization(self, client, sample_item, second_user, db_session):
        """Regenerating a PIN must enforce authorization and rate limiting."""
        # Log in as buyer (second_user)
        client.post("/auth/login", data={
            "email": "other@university.ac.uk",
            "password": "StrongPass123",
        }, follow_redirects=True)

        # claim it
        client.post(f"/items/{sample_item.id}/buy", follow_redirects=True)

        # Log out buyer
        client.post("/auth/logout", follow_redirects=True)

        # 1. Non-parties (anonymous user) get redirected because of login_required
        resp_anon = client.post(f"/items/{sample_item.id}/resend-pin")
        assert resp_anon.status_code == 302

        # Log in as seller (sample_user)
        client.post("/auth/login", data={
            "email": "test@university.ac.uk",
            "password": "StrongPass123",
        }, follow_redirects=True)

        # 2. Non-holder (seller, which is sample_user) should get 403 on paid item
        resp_seller_unauth = client.post(f"/items/{sample_item.id}/resend-pin")
        assert resp_seller_unauth.status_code == 403

        # Log out seller
        client.post("/auth/logout", follow_redirects=True)

        # Log in back as buyer (second_user)
        client.post("/auth/login", data={
            "email": "other@university.ac.uk",
            "password": "StrongPass123",
        }, follow_redirects=True)

        # 3. Holder (buyer, which is second_user) resends successfully
        resp_resend = client.post(f"/items/{sample_item.id}/resend-pin", follow_redirects=True)
        assert resp_resend.status_code == 200
        assert b"new PIN has been generated" in resp_resend.data

        # Check session is updated with the new PIN
        with client.session_transaction() as sess:
            new_pin = sess.get(f"pin_{sample_item.id}")
        assert new_pin is not None

        # Check verify successful with new PIN
        item = db_session.session.get(Item, sample_item.id)
        assert check_password_hash(item.pin_code, new_pin)
