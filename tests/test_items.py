"""
Reuni — Item Route Tests
Covers CRUD operations, buy/claim logic, kg saved awarding, and ownership guards.
"""

from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

from app.models import Item, User, CATEGORIES, CATEGORY_WEIGHTS
from tests.conftest import make_test_image
from unittest.mock import patch, MagicMock


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
        assert b"price greater than zero" in resp_create.data

        # Edit negative price
        resp_edit = auth_client.post(f"/items/{sample_item.id}/edit", data={
            "title": "Test Textbook",
            "description": "Updated description",
            "category": "Books",
            "condition": "Good",
            "price": "-5.00",
        }, content_type="multipart/form-data", follow_redirects=True)
        assert b"price greater than zero" in resp_edit.data


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


class TestNaNPriceSubmissions:

    def test_nan_price_create_and_edit(self, auth_client, sample_item):
        """NaN and infinity prices should be rejected on create and edit routes."""
        # Create NaN price
        resp_create_nan = auth_client.post("/items/new", data={
            "title": "NaN Price Item",
            "description": "Test",
            "category": "Electronics",
            "condition": "New",
            "price": "nan",
            "image": (make_test_image(), "test.jpg")
        }, content_type="multipart/form-data", follow_redirects=True)
        assert b"Please enter a valid price." in resp_create_nan.data

        # Create Inf price
        resp_create_inf = auth_client.post("/items/new", data={
            "title": "Inf Price Item",
            "description": "Test",
            "category": "Electronics",
            "condition": "New",
            "price": "inf",
            "image": (make_test_image(), "test.jpg")
        }, content_type="multipart/form-data", follow_redirects=True)
        assert b"Please enter a valid price." in resp_create_inf.data

        # Edit NaN price
        resp_edit_nan = auth_client.post(f"/items/{sample_item.id}/edit", data={
            "title": "Test Textbook",
            "description": "Updated description",
            "category": "Books",
            "condition": "Good",
            "price": "nan",
        }, content_type="multipart/form-data", follow_redirects=True)
        assert b"Please enter a valid price." in resp_edit_nan.data

    def test_nan_price_search_filters(self, client, db_session):
        """Search filters with NaN or Inf prices should ignore the filter cleanly."""
        resp_nan = client.get("/?min_price=nan&max_price=inf")
        assert resp_nan.status_code == 200


class TestCloudflareR2Integration:

    @patch("boto3.client")
    def test_save_image_to_r2(self, mock_boto_client, app):
        """When STORAGE_PROVIDER is r2, _save_image should upload the file to Cloudflare R2."""
        from app.routes.items import _save_image
        from tests.conftest import make_test_image
        from werkzeug.datastructures import FileStorage
        import io
        from botocore.config import Config
        
        # Configure app for R2
        app.config["STORAGE_PROVIDER"] = "r2"
        app.config["CF_R2_ACCESS_KEY_ID"] = "test-key"
        app.config["CF_R2_SECRET_ACCESS_KEY"] = "test-secret"
        app.config["CF_R2_ENDPOINT_URL"] = "https://test-endpoint.com"
        app.config["CF_R2_BUCKET_NAME"] = "test-bucket"
        app.config["CF_R2_PUBLIC_URL"] = "https://cdn.test.com"

        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        # Prepare dummy file storage upload
        file_io = make_test_image()
        file_storage = FileStorage(stream=file_io, filename="my_test_image.jpg", content_type="image/jpeg")

        with app.app_context():
            filename = _save_image(file_storage)
            
            assert filename is not None
            assert filename.endswith(".webp")
            
            # Verify boto3.client('s3', ...) was initialized correctly
            # We fetch call arguments to check custom configuration
            mock_boto_client.assert_called_once()
            called_kwargs = mock_boto_client.call_args[1]
            assert called_kwargs["endpoint_url"] == "https://test-endpoint.com"
            assert called_kwargs["aws_access_key_id"] == "test-key"
            assert called_kwargs["aws_secret_access_key"] == "test-secret"
            assert called_kwargs["config"].signature_version == "s3v4"
            
            # Verify upload_fileobj was called on the mock client
            mock_s3.upload_fileobj.assert_called_once()
            call_args = mock_s3.upload_fileobj.call_args[0]
            # First arg: buffer
            assert isinstance(call_args[0], io.BytesIO)
            # Second arg: bucket name
            assert call_args[1] == "test-bucket"
            # Third arg: filename
            assert call_args[2] == filename
            
            # Verify content-type was passed correctly in ExtraArgs
            kwargs = mock_s3.upload_fileobj.call_args[1]
            assert kwargs["ExtraArgs"]["ContentType"] == "image/webp"

    @patch("boto3.client")
    def test_delete_image_from_r2(self, mock_boto_client, app):
        """When STORAGE_PROVIDER is r2, _delete_image should delete user uploads from R2."""
        from app.routes.items import _delete_image
        
        app.config["STORAGE_PROVIDER"] = "r2"
        app.config["CF_R2_ACCESS_KEY_ID"] = "test-key"
        app.config["CF_R2_SECRET_ACCESS_KEY"] = "test-secret"
        app.config["CF_R2_ENDPOINT_URL"] = "https://test-endpoint.com"
        app.config["CF_R2_BUCKET_NAME"] = "test-bucket"

        mock_s3 = MagicMock()
        mock_boto_client.return_value = mock_s3

        with app.app_context():
            # 1. Deleting a user-uploaded image should trigger R2 API call
            _delete_image("uuid_filename.webp")
            mock_s3.delete_object.assert_called_once_with(
                Bucket="test-bucket",
                Key="uuid_filename.webp"
            )
            
            # 2. Deleting a seed image should also trigger R2 API call in R2 mode
            mock_s3.reset_mock()
            _delete_image("seed_image.webp")
            mock_s3.delete_object.assert_called_once_with(
                Bucket="test-bucket",
                Key="seed_image.webp"
            )
