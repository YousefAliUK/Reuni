"""
Reuni — Item Route Tests
Covers CRUD operations, buy/claim logic, kg saved awarding, and ownership guards.
"""

from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

from app.models import Item, User, CATEGORIES, CATEGORY_WEIGHTS
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

    def test_image_upload_oversized(self, auth_client):
        """POST /items/new with oversized image (> 5MB) should redirect and flash error via 413 handler."""
        import io
        large_data = b"0" * (6 * 1024 * 1024)  # 6 MB
        resp = auth_client.post("/items/new", data={
            "title": "Oversized Item",
            "description": "Test",
            "category": "Electronics",
            "condition": "New",
            "price": "10.00",
            "image": (io.BytesIO(large_data), "large.jpg")
        }, content_type="multipart/form-data", follow_redirects=True)
        assert resp.status_code == 200
        assert b"Image too large" in resp.data

    def test_image_upload_invalid_mime(self, auth_client):
        """POST /items/new with fake JPG (txt file) should be rejected by PIL validation."""
        import io
        fake_jpg = b"Not a real image format data block"
        resp = auth_client.post("/items/new", data={
            "title": "Fake Image Item",
            "description": "Test",
            "category": "Electronics",
            "condition": "New",
            "price": "10.00",
            "image": (io.BytesIO(fake_jpg), "fake.jpg")
        }, content_type="multipart/form-data", follow_redirects=True)
        assert b"valid photo" in resp.data

    def test_description_length_validation(self, auth_client):
        """Description over 2000 characters should be rejected."""
        img = make_test_image()
        long_desc = "x" * 2001
        resp = auth_client.post("/items/new", data={
            "title": "Long Description Item",
            "description": long_desc,
            "category": "Electronics",
            "condition": "New",
            "price": "10.00",
            "image": (img, "test.jpg")
        }, content_type="multipart/form-data", follow_redirects=True)
        assert b"Description must be 2000 characters or fewer" in resp.data


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

    def test_negative_price_submissions(self, auth_client, sample_item):
        """Negative prices should be rejected on create and edit routes."""
        img = make_test_image()
        # Create negative price
        resp_create = auth_client.post("/items/new", data={
            "title": "Negative Price Item",
            "description": "Test",
            "category": "Electronics",
            "condition": "New",
            "price": "-10.00",
            "image": (img, "test.jpg")
        }, content_type="multipart/form-data", follow_redirects=True)
        assert b"Price cannot be negative" in resp_create.data

        # Edit negative price
        resp_edit = auth_client.post(f"/items/{sample_item.id}/edit", data={
            "title": "Test Textbook",
            "description": "Updated description",
            "category": "Books",
            "condition": "Good",
            "price": "-5.00",
        }, content_type="multipart/form-data", follow_redirects=True)
        assert b"Price cannot be negative" in resp_edit.data


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


class TestCategoryWeightsAPI:

    def test_category_weights_api_returns_json(self, client):
        """GET /items/api/category-weights should return 200 with JSON."""
        resp = client.get("/items/api/category-weights")
        assert resp.status_code == 200
        assert resp.content_type == "application/json"

    def test_category_weights_api_values(self, client):
        """Response should contain all categories with correct weight values."""
        resp = client.get("/items/api/category-weights")
        data = resp.get_json()

        for cat in CATEGORIES:
            assert cat in data, f"Missing category: {cat}"
            assert data[cat] == CATEGORY_WEIGHTS[cat]

    def test_category_weights_api_count(self, client):
        """API should return exactly the same number of entries as CATEGORIES."""
        resp = client.get("/items/api/category-weights")
        data = resp.get_json()
        assert len(data) == len(CATEGORIES)
