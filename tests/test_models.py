"""
Reuni — Model Tests
Verifies User and Item ORM models, relationships, and constants.
"""

from app.models import User, Item, CATEGORIES, CATEGORY_WEIGHTS, CONDITION_CHOICES


class TestUserModel:

    def test_set_and_check_password(self, db_session):
        """Password hashing should verify correct passwords and reject wrong ones."""
        user = User(email="pw@test.ac.uk", name="PW Test", phone_number="+447700100007")
        user.set_password("correct-horse")
        assert user.check_password("correct-horse") is True
        assert user.check_password("wrong-password") is False

    def test_default_kg_saved_total(self, db_session):
        """A new user should start with 0.0 kg saved."""
        user = User(email="eco@test.ac.uk", name="Eco Test", phone_number="+447700100008")
        user.set_password("pass")
        db_session.session.add(user)
        db_session.session.commit()
        assert user.kg_saved_total == 0.0

    def test_user_repr(self, sample_user):
        """User repr should contain the email address."""
        assert "test@university.ac.uk" in repr(sample_user)

    def test_user_created_at(self, sample_user):
        """User should have a created_at timestamp."""
        assert sample_user.created_at is not None


class TestItemModel:

    def test_item_defaults(self, sample_item):
        """A new item should default to unsold with no buyer and default PIN settings."""
        assert sample_item.is_sold is False
        assert sample_item.buyer_id is None
        assert sample_item.claimed_at is None
        assert sample_item.pin_code is None
        assert sample_item.pin_expires_at is None
        assert sample_item.pin_attempts == 0

    def test_item_seller_relationship(self, sample_item, sample_user):
        """item.seller should return the correct User object."""
        assert sample_item.seller.id == sample_user.id
        assert sample_item.seller.email == "test@university.ac.uk"

    def test_item_repr(self, sample_item):
        """Item repr should contain the title."""
        assert "Test Textbook" in repr(sample_item)

    def test_item_created_at(self, sample_item):
        """Item should have a created_at timestamp."""
        assert sample_item.created_at is not None

    def test_image_url_resolution(self, sample_item, app):
        """image_url should dynamically resolve based on STORAGE_PROVIDER and prefix."""
        with app.test_request_context():
            # 1. Test None value
            sample_item.image_filename = None
            assert sample_item.image_url is None

            # 2. Test Local Storage Provider (default behavior)
            app.config["STORAGE_PROVIDER"] = "local"
            sample_item.image_filename = "uuid_filename.webp"
            assert sample_item.image_url == "/static/uploads/uuid_filename.webp"
            
            sample_item.image_filename = "seed_image.webp"
            assert sample_item.image_url == "/static/uploads/seed_image.webp"

            # 3. Test R2 Storage Provider
            app.config["STORAGE_PROVIDER"] = "r2"
            app.config["CF_R2_PUBLIC_URL"] = "https://cdn.reuni.app"
            
            # Both user and seed images should resolve uniformly to R2
            sample_item.image_filename = "uuid_filename.webp"
            assert sample_item.image_url == "https://cdn.reuni.app/uuid_filename.webp"

            sample_item.image_filename = "seed_image.webp"
            assert sample_item.image_url == "https://cdn.reuni.app/seed_image.webp"


class TestConstants:

    def test_categories_and_weights_match(self):
        """Every CATEGORIES entry must have a corresponding CATEGORY_WEIGHTS value."""
        for cat in CATEGORIES:
            assert cat in CATEGORY_WEIGHTS, f"Category '{cat}' missing from CATEGORY_WEIGHTS"
            assert isinstance(CATEGORY_WEIGHTS[cat], (int, float))

    def test_condition_choices_not_empty(self):
        """CONDITION_CHOICES should contain at least one value."""
        assert len(CONDITION_CHOICES) > 0

    def test_categories_not_empty(self):
        """CATEGORIES should contain at least one value."""
        assert len(CATEGORIES) > 0
