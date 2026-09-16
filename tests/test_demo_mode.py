"""
Reuni — Demo Mode Tests
Verifies read-only constraints and notifications when DEMO_MODE is active.
"""

from app.models import User, Item


def test_demo_mode_registration_blocked(client, app):
    """POST /auth/register should redirect to login and prevent account creation in demo mode."""
    app.config["DEMO_MODE"] = True
    try:
        resp = client.post(
            "/auth/register",
            data={
                "name": "Demo Test User",
                "email": "demo.tester@brookes.ac.uk",
                "password": "Password123!",
                "confirm_password": "Password123!",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Registration is disabled in demo mode" in resp.data
        user = User.query.filter_by(email="demo.tester@brookes.ac.uk").first()
        assert user is None
    finally:
        app.config["DEMO_MODE"] = False


def test_demo_mode_registration_notice_on_get(client, app):
    """GET /auth/register should display portfolio demo notice when DEMO_MODE is true."""
    app.config["DEMO_MODE"] = True
    try:
        resp = client.get("/auth/register")
        assert resp.status_code == 200
        assert b"Portfolio Demo Mode: Account registration is disabled" in resp.data
    finally:
        app.config["DEMO_MODE"] = False


def test_demo_mode_item_creation_blocked(client, app, db_session):
    """POST /items/new should block listing creation when DEMO_MODE is true."""
    user = User(
        name="Test Seller",
        email="seller@brookes.ac.uk",
        university_domain="brookes.ac.uk",
        is_verified=True,
    )
    user.set_password("Password123!")
    db_session.session.add(user)
    db_session.session.commit()

    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True

    app.config["DEMO_MODE"] = True
    try:
        resp = client.post(
            "/items/new",
            data={
                "title": "Blocked Demo Item",
                "description": "This should not be saved",
                "category": "Electronics",
                "condition": "Good",
                "price": "10.00",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"Listing creation is disabled in demo mode" in resp.data
        item = Item.query.filter_by(title="Blocked Demo Item").first()
        assert item is None
    finally:
        app.config["DEMO_MODE"] = False


def test_demo_mode_chat_sending_blocked(client, app, db_session):
    """POST /messages/<item_id>/send should return error in demo mode."""
    seller = User(name="Seller", email="s@brookes.ac.uk", university_domain="brookes.ac.uk", is_verified=True)
    seller.set_password("Pass1234!")
    buyer = User(name="Buyer", email="b@brookes.ac.uk", university_domain="brookes.ac.uk", is_verified=True)
    buyer.set_password("Pass1234!")
    db_session.session.add_all([seller, buyer])
    db_session.session.commit()

    item = Item(
        title="Chat Demo Item",
        description="Testing chat",
        category="Books",
        condition="Good",
        price=5.0,
        seller_id=seller.id,
        buyer_id=buyer.id,
        university_domain="brookes.ac.uk",
    )
    db_session.session.add(item)
    db_session.session.commit()

    with client.session_transaction() as sess:
        sess["_user_id"] = str(buyer.id)
        sess["_fresh"] = True

    app.config["DEMO_MODE"] = True
    try:
        resp = client.post(
            f"/api/messages/{item.id}/send",
            json={"content": "Hello in demo mode"},
        )
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "Sending messages is disabled in demo mode."
    finally:
        app.config["DEMO_MODE"] = False


def test_demo_mode_footer_notice(client, app):
    """Footer should display subtle demo notice when DEMO_MODE is true."""
    app.config["DEMO_MODE"] = True
    try:
        resp = client.get("/")
        assert resp.status_code == 200
        assert b"Portfolio Demo" in resp.data
        assert b"Sample Data" in resp.data
    finally:
        app.config["DEMO_MODE"] = False
