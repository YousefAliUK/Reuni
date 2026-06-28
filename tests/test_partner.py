import pytest
from datetime import datetime, timezone, timedelta
from flask import session
from app import db
from app.models import User, Item
from app.utils.tokens import generate_partner_invite_token

def test_partner_registration_via_invite(client, app):
    """Test registering a partner account via a valid invite link."""
    with app.app_context():
        token = generate_partner_invite_token("brookes.ac.uk", app.config["SECRET_KEY"])
        
    # GET register page
    resp = client.get(f"/auth/invite/{token}")
    assert resp.status_code == 200
    assert b"Create Partner Account" in resp.data
    assert b"brookes.ac.uk" in resp.data

    # POST registration
    resp = client.post(
        f"/auth/invite/{token}",
        data={
            "name": "Partner User",
            "email": "staff.member@brookes.ac.uk",
            "password": "Password123",
            "confirm_password": "Password123",
        },
        follow_redirects=True
    )
    assert resp.status_code == 200
    assert b"Partner account created. You can now log in." in resp.data

    # Verify database entry
    with app.app_context():
        user = User.query.filter_by(email="staff.member@brookes.ac.uk").first()
        assert user is not None
        assert user.role == "partner"
        assert user.partner_university == "brookes.ac.uk"
        assert user.is_verified is True

def test_partner_registration_validation(client, app):
    """Test domain and password validation during registration."""
    with app.app_context():
        token = generate_partner_invite_token("brookes.ac.uk", app.config["SECRET_KEY"])

    # Wrong domain email
    resp = client.post(
        f"/auth/invite/{token}",
        data={
            "name": "Partner User",
            "email": "staff.member@oxford.ac.uk",
            "password": "Password123",
            "confirm_password": "Password123",
        },
        follow_redirects=True
    )
    assert b"Please use your institutional email address for brookes.ac.uk." in resp.data

    # Mismatched passwords
    resp = client.post(
        f"/auth/invite/{token}",
        data={
            "name": "Partner User",
            "email": "staff.member@brookes.ac.uk",
            "password": "Password123",
            "confirm_password": "differentpassword",
        },
        follow_redirects=True
    )
    assert b"Passwords do not match." in resp.data

    # Name too long (over 80 characters)
    resp_name_too_long = client.post(
        f"/auth/invite/{token}",
        data={
            "name": "a" * 81,
            "email": "staff.member@brookes.ac.uk",
            "password": "password123",
            "confirm_password": "password123",
        },
        follow_redirects=True
    )
    assert b"Name must be 80 characters or fewer" in resp_name_too_long.data

def test_partner_dashboard_scoping(client, app, db_session):
    """Test that the partner dashboard displays correct, scoped statistics."""
    with app.app_context():
        student_brookes = User(name="Brookes Student", email="stud@brookes.ac.uk", is_verified=True, university_domain="brookes.ac.uk")
        student_brookes.set_password("password123")
        student_oxford = User(name="Oxford Student", email="stud@oxford.ac.uk", is_verified=True, university_domain="oxford.ac.uk")
        student_oxford.set_password("password123")
        
        partner_brookes = User(name="Brookes Partner", email="partner@brookes.ac.uk", role="partner", partner_university="brookes.ac.uk", is_verified=True, is_active=True)
        partner_brookes.set_password("password123")
        
        db.session.add_all([student_brookes, student_oxford, partner_brookes])
        db.session.commit()

        # Create scoped items
        item_brookes = Item(title="Brookes Desk", category="Furniture", condition="Good", price=10.0, is_sold=True, kg_saved=12.0, seller_id=student_brookes.id, university_domain="brookes.ac.uk")
        item_oxford = Item(title="Oxford Sofa", category="Furniture", condition="Good", price=20.0, is_sold=True, kg_saved=15.0, seller_id=student_oxford.id, university_domain="oxford.ac.uk")
        
        db.session.add_all([item_brookes, item_oxford])
        db.session.commit()

    # Login as Brookes Partner
    client.post("/auth/login", data={"email": "partner@brookes.ac.uk", "password": "password123"}, follow_redirects=True)

    # Access dashboard
    resp = client.get("/partner/dashboard")
    assert resp.status_code == 200
    
    # Assert data is scoped (Brookes statistics only)
    assert b"1" in resp.data  # Exchanged items count (Brookes=1, Oxford=1)
    assert b"12.0" in resp.data  # kg saved (Brookes=12.0)
    assert b"Furniture" in resp.data
    assert b"1 exchanged" in resp.data
    assert b"Global Sustainability Dashboard" not in resp.data

def test_student_and_partner_routing_protection(client, app, db_session):
    """Test that students cannot access partner routes, and partners cannot access student marketplace features."""
    with app.app_context():
        student = User(name="Student", email="stud@brookes.ac.uk", is_verified=True, university_domain="brookes.ac.uk")
        student.set_password("password123")
        
        partner = User(name="Partner", email="partner@brookes.ac.uk", role="partner", partner_university="brookes.ac.uk", is_verified=True, is_active=True)
        partner.set_password("password123")
        
        db.session.add_all([student, partner])
        db.session.commit()

    # 1. Student trying to access partner dashboard
    client.post("/auth/login", data={"email": "stud@brookes.ac.uk", "password": "password123"}, follow_redirects=True)
    resp = client.get("/partner/dashboard", follow_redirects=True)
    assert b"You do not have permission to access the partner dashboard." in resp.data

    # 2. Partner trying to list an item (should succeed)
    client.post("/auth/logout", follow_redirects=True)
    client.post("/auth/login", data={"email": "partner@brookes.ac.uk", "password": "password123"}, follow_redirects=True)
    resp = client.get("/items/new", follow_redirects=True)
    assert resp.status_code == 200
    assert b"List an Item" in resp.data

def test_session_expiry_and_deactivation(client, app, db_session):
    """Test partner 7-day session expiry rules and immediate deactivation behavior."""
    with app.app_context():
        partner = User(name="Partner", email="partner@brookes.ac.uk", role="partner", partner_university="brookes.ac.uk", is_verified=True, is_active=True)
        partner.set_password("password123")
        db.session.add(partner)
        db.session.commit()

    # Login partner
    client.post("/auth/login", data={"email": "partner@brookes.ac.uk", "password": "password123"}, follow_redirects=True)
    
    # 1. Access dashboard when logged in (should succeed)
    resp = client.get("/partner/dashboard")
    assert resp.status_code == 200

    # 2. Simulate session age = 8 days
    with client.session_transaction() as sess:
        sess['logged_in_at'] = (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=8)).isoformat()

    # Request dashboard (should log out and redirect)
    resp = client.get("/partner/dashboard", follow_redirects=True)
    assert b"Your session has expired. Please log in again." in resp.data

    # 3. Simulate missing logged_in_at timestamp (legacy session, should allow through)
    client.post("/auth/login", data={"email": "partner@brookes.ac.uk", "password": "password123"}, follow_redirects=True)
    with client.session_transaction() as sess:
        sess.pop('logged_in_at', None)
    resp = client.get("/partner/dashboard", follow_redirects=True)
    assert resp.status_code == 200

    # 4. Immediate deactivation check
    client.post("/auth/login", data={"email": "partner@brookes.ac.uk", "password": "password123"}, follow_redirects=True)
    with app.app_context():
        p_user = User.query.filter_by(email="partner@brookes.ac.uk").first()
        p_user.is_active = False
        db.session.commit()

    # Access page (should be kicked out instantly)
    resp = client.get("/partner/dashboard", follow_redirects=True)
    assert b"Your account has been deactivated. Contact support." in resp.data

def test_partner_marketplace_dashboard(client, app, db_session):
    """Test that a partner accessing /dashboard reaches the regular marketplace dashboard rather than being redirected."""
    with app.app_context():
        partner = User(
            name="Marketplace Partner",
            email="partner@brookes.ac.uk",
            role="partner",
            partner_university="brookes.ac.uk",
            is_verified=True,
            is_active=True
        )
        partner.set_password("password123")
        db.session.add(partner)
        db.session.commit()

    # Log in
    client.post("/auth/login", data={"email": "partner@brookes.ac.uk", "password": "password123"}, follow_redirects=True)

    # Get /dashboard (should load normally, return 200, and show "My Listings")
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 200
    assert b"My Listings" in resp.data
