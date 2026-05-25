"""
UniCycle — Item Route Tests
Covers CRUD operations, buy/claim logic, kg saved awarding, and ownership guards.
"""

from datetime import datetime, timezone, timedelta

from app.models import Item, User
from tests.conftest import make_test_image


class TestItemDetail:

    def test_item_detail_page(self, client, sample_item):
        """GET /items/<id> should show the item title."""
        resp = client.get(f"/items/{sample_item.id}")
        assert resp.status_code == 200
        assert b"Test Textbook" in resp.data

    def test_item_detail_404(self, client):
        """GET /items/9999 for a non-existent item should return 404."""
        resp = client.get("/items/9999")
        assert resp.status_code == 404


class TestListItem:

    def test_list_item_requires_login(self, client):
        """GET /items/new unauthenticated should redirect to login."""
        resp = client.get("/items/new", follow_redirects=False)
        assert resp.status_code == 302
        assert "/auth/login" in resp.headers["Location"]

    def test_list_item_page_loads(self, auth_client):
        """GET /items/new authenticated should return 200."""
        resp = auth_client.get("/items/new")
        assert resp.status_code == 200
        assert b"List an Item" in resp.data

    def test_list_item_success(self, auth_client, db_session):
        """POST /items/new with valid data should create an item."""
        img = make_test_image()
        resp = auth_client.post("/items/new", data={
            "title": "New Test Item",
            "description": "A brand new item",
            "category": "Electronics",
            "condition": "New",
            "price": "99.99",
            "image": (img, "test.jpg"),
        }, content_type="multipart/form-data", follow_redirects=False)
        assert resp.status_code == 302  # redirect to detail

        item = Item.query.filter_by(title="New Test Item").first()
        assert item is not None
        assert item.category == "Electronics"
        assert item.kg_saved == 3.0
        assert item.is_sold is False

    def test_list_item_invalid_category(self, auth_client):
        """POST /items/new with invalid category should flash error."""
        img = make_test_image()
        resp = auth_client.post("/items/new", data={
            "title": "Bad Category Item",
            "description": "Test",
            "category": "InvalidCategory",
            "condition": "New",
            "price": "10",
            "image": (img, "test.jpg"),
        }, content_type="multipart/form-data", follow_redirects=True)
        assert b"required fields" in resp.data

    def test_list_item_missing_image(self, auth_client):
        """POST /items/new without image should flash error."""
        resp = auth_client.post("/items/new", data={
            "title": "No Image Item",
            "description": "Test",
            "category": "Books",
            "condition": "Good",
            "price": "5",
        }, content_type="multipart/form-data", follow_redirects=True)
        assert b"valid photo" in resp.data

    def test_list_free_item(self, auth_client, db_session):
        """POST /items/new with is_free=on should set price to 0."""
        img = make_test_image()
        resp = auth_client.post("/items/new", data={
            "title": "Free Stationery",
            "description": "Free stuff",
            "category": "Stationery",
            "condition": "Good",
            "is_free": "on",
            "price": "0",
            "image": (img, "freebie.jpg"),
        }, content_type="multipart/form-data", follow_redirects=False)
        assert resp.status_code == 302

        item = Item.query.filter_by(title="Free Stationery").first()
        assert item is not None
        assert item.is_free is True
        assert item.price == 0.0


class TestEditItem:

    def test_edit_item_by_owner(self, auth_client, sample_item):
        """Owner should be able to view the edit page."""
        resp = auth_client.get(f"/items/{sample_item.id}/edit")
        assert resp.status_code == 200
        assert b"Edit Listing" in resp.data

    def test_edit_item_by_non_owner(self, second_auth_client, sample_item):
        """Non-owner should be denied access and redirected."""
        resp = second_auth_client.get(
            f"/items/{sample_item.id}/edit", follow_redirects=True
        )
        assert b"your own items" in resp.data

    def test_edit_sold_item(self, auth_client, sample_item, db_session):
        """Editing a sold item should be blocked."""
        sample_item.is_sold = True
        db_session.session.commit()
        resp = auth_client.get(
            f"/items/{sample_item.id}/edit", follow_redirects=True
        )
        assert b"already been sold" in resp.data

    def test_edit_item_submit(self, auth_client, sample_item, db_session):
        """POST should update the item fields."""
        resp = auth_client.post(f"/items/{sample_item.id}/edit", data={
            "title": "Updated Title",
            "description": "Updated description",
            "category": "Electronics",
            "condition": "Like New",
            "price": "200.00",
        }, content_type="multipart/form-data", follow_redirects=True)
        assert b"updated successfully" in resp.data

        item = db_session.session.get(Item, sample_item.id)
        assert item.title == "Updated Title"
        assert item.category == "Electronics"
        assert item.kg_saved == 3.0  # Electronics weight


class TestDeleteItem:

    def test_delete_item_by_owner(self, auth_client, sample_item, db_session):
        """Owner should be able to delete their unsold item."""
        item_id = sample_item.id
        resp = auth_client.post(
            f"/items/{item_id}/delete", follow_redirects=True
        )
        assert b"deleted" in resp.data
        assert db_session.session.get(Item, item_id) is None

    def test_delete_item_by_non_owner(self, second_auth_client, sample_item, db_session):
        """Non-owner should be denied deletion."""
        resp = second_auth_client.post(
            f"/items/{sample_item.id}/delete", follow_redirects=True
        )
        assert b"your own items" in resp.data
        assert db_session.session.get(Item, sample_item.id) is not None

    def test_delete_sold_item(self, auth_client, sample_item, db_session):
        """Deleting a sold item should be blocked."""
        sample_item.is_sold = True
        db_session.session.commit()
        resp = auth_client.post(
            f"/items/{sample_item.id}/delete", follow_redirects=True
        )
        assert b"already been sold" in resp.data


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
        assert len(item.pin_code) == 4
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
        sample_item.pin_code = "1234"
        db_session.session.commit()

        resp = auth_client.get(f"/items/{sample_item.id}/edit", follow_redirects=True)
        assert b"while a handshake is pending" in resp.data

    def test_cannot_delete_while_pending(self, auth_client, sample_item, second_user, db_session):
        """Deleting an item with a pending claim should be blocked."""
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = "1234"
        db_session.session.commit()

        resp = auth_client.post(f"/items/{sample_item.id}/delete", follow_redirects=True)
        assert b"while a handshake is pending" in resp.data

    def test_pin_page_access_guard(self, client, sample_item, second_user, db_session):
        """Users other than buyer or seller cannot access the PIN page."""
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = "1234"
        db_session.session.commit()

        # Try to access pin page anonymously or as a third user
        resp = client.get(f"/items/{sample_item.id}/pin", follow_redirects=True)
        # Should redirect to login or show access denied
        assert b"Log In" in resp.data

    def test_confirm_pin_success(self, second_auth_client, sample_item, sample_user, second_user, db_session):
        """Confirming the correct PIN should mark item sold and credit seller's total kg saved."""
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = "4321"
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
        sample_item.pin_code = "9999"
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

    def test_cancel_claim(self, second_auth_client, sample_item, second_user, db_session):
        """A user (buyer or seller) should be able to manually cancel a claim."""
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = "1111"
        db_session.session.commit()

        resp = second_auth_client.post(f"/items/{sample_item.id}/cancel-claim", follow_redirects=True)
        assert b"has been cancelled" in resp.data

        item = db_session.session.get(Item, sample_item.id)
        assert item.buyer_id is None
        assert item.pin_code is None
        assert item.is_sold is False

    def test_pin_page_seller_sees_pin_free_item(self, auth_client, sample_item, second_user, db_session):
        """For free items, seller should see the PIN code on the PIN page."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = "5678"
        sample_item.is_free = True
        sample_item.claimed_at = now
        sample_item.pin_expires_at = now + timedelta(hours=72)
        db_session.session.commit()

        resp = auth_client.get(f"/items/{sample_item.id}/pin")
        assert resp.status_code == 200
        for digit in "5678":
            assert digit.encode() in resp.data
        assert b"Your PIN Code" in resp.data

    def test_pin_page_buyer_sees_pin_paid_item(self, second_auth_client, sample_item, second_user, db_session):
        """For paid items, buyer should see the PIN code on the PIN page."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = "4321"
        sample_item.is_free = False
        sample_item.claimed_at = now
        sample_item.pin_expires_at = now + timedelta(hours=72)
        db_session.session.commit()

        resp = second_auth_client.get(f"/items/{sample_item.id}/pin")
        assert resp.status_code == 200
        for digit in "4321":
            assert digit.encode() in resp.data
        assert b"Your PIN Code" in resp.data

    def test_pin_page_shows_seller_phone(self, second_auth_client, sample_item, sample_user, second_user, db_session):
        """Buyer should see the seller's phone number and WhatsApp link on the PIN page."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = "1234"
        sample_item.claimed_at = now
        sample_item.pin_expires_at = now + timedelta(hours=72)
        db_session.session.commit()

        resp = second_auth_client.get(f"/items/{sample_item.id}/pin")
        assert resp.status_code == 200
        assert sample_user.phone_number.encode() in resp.data
        assert b"wa.me" in resp.data

    def test_expired_pin_auto_cancels(self, auth_client, sample_item, second_user, db_session):
        """Visiting PIN page after 72h should auto-cancel the claim."""
        past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=73)
        sample_item.buyer_id = second_user.id
        sample_item.pin_code = "1234"
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
        sample_item.pin_code = "1234"
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
        sample_item.pin_code = "1234"
        db_session.session.commit()

        # Create a third user and try to claim
        third = User(email="third@university.ac.uk", name="Third User", phone_number="+447700100009")
        third.set_password("password123")
        db_session.session.add(third)
        db_session.session.commit()

        third_client = app.test_client()
        third_client.post("/auth/login", data={
            "email": "third@university.ac.uk",
            "password": "password123",
        }, follow_redirects=True)

        resp = third_client.post(f"/items/{sample_item.id}/buy", follow_redirects=True)
        assert b"pending claim" in resp.data or b"has been sold" in resp.data
