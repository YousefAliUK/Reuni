import pytest
from app import db
from app.models import User, Item

def test_admin_access_control(client, app, db_session):
    """Test that only admins can access administrative routes."""
    with app.app_context():
        admin = User(name="Admin", email="admin@brookes.ac.uk", role="admin", is_verified=True, is_active=True)
        admin.set_password("StrongPass123")
        
        partner = User(name="Partner", email="partner@brookes.ac.uk", role="partner", partner_university="brookes.ac.uk", is_verified=True, is_active=True)
        partner.set_password("StrongPass123")
        
        student = User(name="Student", email="student@brookes.ac.uk", is_verified=True, university_domain="brookes.ac.uk")
        student.set_password("StrongPass123")
        
        db.session.add_all([admin, partner, student])
        db.session.commit()

    # 1. Partner accesses /admin/partners -> should get 403
    client.post("/auth/login", data={"email": "partner@brookes.ac.uk", "password": "StrongPass123"}, follow_redirects=True)
    resp = client.get("/admin/partners")
    assert resp.status_code == 403

    # 2. Student accesses /admin/partners -> should get 403
    client.post("/auth/logout", follow_redirects=True)
    client.post("/auth/login", data={"email": "student@brookes.ac.uk", "password": "StrongPass123"}, follow_redirects=True)
    resp = client.get("/admin/partners")
    assert resp.status_code == 403

    # 3. Admin accesses /admin/partners -> should get 200
    client.post("/auth/logout", follow_redirects=True)
    client.post("/auth/login", data={"email": "admin@brookes.ac.uk", "password": "StrongPass123"}, follow_redirects=True)
    resp = client.get("/admin/partners")
    assert resp.status_code == 200
    assert b"Admin Control Panel" in resp.data

def test_admin_invite_generation(client, app, db_session):
    """Test that admins can generate partner invite URLs."""
    with app.app_context():
        admin = User(name="Admin", email="admin@brookes.ac.uk", role="admin", is_verified=True, is_active=True)
        admin.set_password("StrongPass123")
        db.session.add(admin)
        db.session.commit()

    client.post("/auth/login", data={"email": "admin@brookes.ac.uk", "password": "StrongPass123"}, follow_redirects=True)

    # Valid domain
    resp = client.post("/admin/partners/invite", data={"university_domain": "brookes.ac.uk"})
    assert resp.status_code == 200
    assert b"Invitation link generated successfully." in resp.data
    assert b"/auth/invite/" in resp.data

    # Valid email address (should extract domain and succeed)
    resp = client.post("/admin/partners/invite", data={"university_domain": "staff.member@brookes.ac.uk"})
    assert resp.status_code == 200
    assert b"Invitation link generated successfully." in resp.data
    assert b"/auth/invite/" in resp.data

    # Invalid domain
    resp = client.post("/admin/partners/invite", data={"university_domain": "invalid-domain.com"}, follow_redirects=True)
    assert b"Please enter a valid .ac.uk university domain." in resp.data

    # Invalid email address
    resp = client.post("/admin/partners/invite", data={"university_domain": "staff.member@invalid-domain.com"}, follow_redirects=True)
    assert b"Please enter a valid .ac.uk university domain." in resp.data

def test_admin_partner_deactivation(client, app, db_session):
    """Test that admins can deactivate partners and cannot deactivate themselves."""
    with app.app_context():
        admin = User(name="Admin", email="admin@brookes.ac.uk", role="admin", is_verified=True, is_active=True)
        admin.set_password("StrongPass123")
        
        partner = User(name="Partner", email="partner@brookes.ac.uk", role="partner", partner_university="brookes.ac.uk", is_verified=True, is_active=True)
        partner.set_password("StrongPass123")
        
        db.session.add_all([admin, partner])
        db.session.commit()
        partner_id = partner.id
        admin_id = admin.id

    client.post("/auth/login", data={"email": "admin@brookes.ac.uk", "password": "StrongPass123"}, follow_redirects=True)

    # Prevent self-deactivation
    resp = client.post(f"/admin/partners/{admin_id}/deactivate", follow_redirects=True)
    assert b"You cannot deactivate your own account." in resp.data
    with app.app_context():
        adm = db.session.get(User, admin_id)
        assert adm.is_active is True

    # Successful deactivation
    resp = client.post(f"/admin/partners/{partner_id}/deactivate", follow_redirects=True)
    assert b"has been deactivated." in resp.data
    with app.app_context():
        part = db.session.get(User, partner_id)
        assert part.is_active is False

def test_admin_global_dashboard(client, app, db_session):
    """Test that admins see global statistics on the partner dashboard when no university is scoped."""
    with app.app_context():
        admin = User(name="Admin", email="admin@reuni.app", role="admin", is_verified=True, is_active=True)
        admin.set_password("StrongPass123")
        
        student_brookes = User(name="Brookes Student", email="stud@brookes.ac.uk", is_verified=True, university_domain="brookes.ac.uk")
        student_brookes.set_password("StrongPass123")
        student_oxford = User(name="Oxford Student", email="stud@oxford.ac.uk", is_verified=True, university_domain="oxford.ac.uk")
        student_oxford.set_password("StrongPass123")
        
        db.session.add_all([admin, student_brookes, student_oxford])
        db.session.commit()

        # Items from different universities
        item_brookes = Item(title="Brookes Desk", category="Furniture", condition="Good", price=10.0, is_sold=True, kg_saved=12.0, seller_id=student_brookes.id, university_domain="brookes.ac.uk")
        item_oxford = Item(title="Oxford Sofa", category="Furniture", condition="Good", price=20.0, is_sold=True, kg_saved=15.0, seller_id=student_oxford.id, university_domain="oxford.ac.uk")
        
        db.session.add_all([item_brookes, item_oxford])
        db.session.commit()

    client.post("/auth/login", data={"email": "admin@reuni.app", "password": "StrongPass123"}, follow_redirects=True)
    
    resp = client.get("/partner/dashboard")
    assert resp.status_code == 200
    assert b"Global Sustainability Dashboard" in resp.data
    # Aggregate data: items = 2, kg_saved = 27.0
    assert b"2" in resp.data
    assert b"27.0" in resp.data

def test_admin_marketplace_dashboard(client, app, db_session):
    """Test that an admin accessing /dashboard reaches the regular marketplace dashboard rather than being redirected to admin panel."""
    with app.app_context():
        admin = User(name="Marketplace Admin", email="admin@brookes.ac.uk", role="admin", is_verified=True, is_active=True)
        admin.set_password("StrongPass123")
        db.session.add(admin)
        db.session.commit()

    # Log in
    client.post("/auth/login", data={"email": "admin@brookes.ac.uk", "password": "StrongPass123"}, follow_redirects=True)

    # Get /dashboard (should load normally, return 200, and show "My Listings")
    resp = client.get("/dashboard", follow_redirects=False)
    assert resp.status_code == 200
    assert b"My Listings" in resp.data
