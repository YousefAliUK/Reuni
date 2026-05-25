"""
UniCycle — Shared Test Fixtures (pytest)
Uses TestingConfig with an in-memory SQLite database.
"""

import io
import pytest
from PIL import Image as PILImage

from app import create_app, db as _db
from app.config import TestingConfig
from app.models import User, Item, CATEGORY_WEIGHTS


@pytest.fixture(scope="session")
def app():
    """Create the Flask application with TestingConfig."""
    _app = create_app(TestingConfig)
    # Disable CSRF for test requests so we don't need tokens in every POST
    _app.config["WTF_CSRF_ENABLED"] = False
    return _app


@pytest.fixture(autouse=True)
def db_session(app):
    """
    Push an app context, create all tables, yield, then drop everything.
    Runs automatically for every test (autouse=True).
    """
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture()
def client(app):
    """Flask test client for making HTTP requests."""
    return app.test_client()


@pytest.fixture()
def sample_user(db_session):
    """Create and return a persisted test user."""
    user = User(email="test@university.ac.uk", name="Test User", phone_number="+447700100005")
    user.set_password("password123")
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture()
def second_user(db_session):
    """Create and return a second test user (for ownership / buy tests)."""
    user = User(email="other@university.ac.uk", name="Other User", phone_number="+447700100006")
    user.set_password("password123")
    db_session.session.add(user)
    db_session.session.commit()
    return user


@pytest.fixture()
def sample_item(db_session, sample_user):
    """Create and return a persisted test item owned by sample_user."""
    item = Item(
        title="Test Textbook",
        description="A test item for unit tests.",
        category="Books",
        condition="Good",
        price=15.00,
        is_free=False,
        image_filename="test_placeholder.jpg",
        kg_saved=CATEGORY_WEIGHTS["Books"],
        seller_id=sample_user.id,
    )
    db_session.session.add(item)
    db_session.session.commit()
    return item


@pytest.fixture()
def auth_client(client, sample_user):
    """Return a test client that is already logged in as sample_user."""
    client.post("/auth/login", data={
        "email": "test@university.ac.uk",
        "password": "password123",
    }, follow_redirects=True)
    return client


@pytest.fixture()
def second_auth_client(app, second_user):
    """Return a test client logged in as second_user."""
    c = app.test_client()
    c.post("/auth/login", data={
        "email": "other@university.ac.uk",
        "password": "password123",
    }, follow_redirects=True)
    return c


def make_test_image(fmt="JPEG", size=(10, 10), color="red"):
    """Generate a tiny in-memory image file for upload tests."""
    img = PILImage.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format=fmt, quality=85)
    buf.seek(0)
    return buf
