import pytest
from datetime import datetime, timezone, timedelta
from app import db
from app.models import User, UniversityConfig, Season

def test_admin_routes_require_admin(client, db_session):
    """Test that non-admin and anonymous users cannot access the university and season admin panels."""
    # Unauthenticated
    assert client.get("/admin/universities").status_code == 302
    assert client.get("/admin/seasons").status_code == 302

    # Authenticated but non-admin (student)
    student = User(
        email="student@brookes.ac.uk",
        name="Student",
        role="student",
        is_verified=True,
    )
    student.set_password("Password123!")
    db_session.session.add(student)
    db_session.session.commit()

    client.post("/auth/login", data={"email": "student@brookes.ac.uk", "password": "Password123!"})

    assert client.get("/admin/universities").status_code == 403
    assert client.get("/admin/seasons").status_code == 403

def test_admin_universities_crud(client, db_session):
    """Test creating and editing university configurations via admin panel."""
    # Create admin user
    admin = User(
        email="admin@reuni.ac.uk",
        name="Admin User",
        role="admin",
        is_verified=True,
    )
    admin.set_password("Password123!")
    db_session.session.add(admin)
    db_session.session.commit()

    client.post("/auth/login", data={"email": "admin@reuni.ac.uk", "password": "Password123!"})

    # 1. Create a config
    resp = client.post("/admin/universities/new", data={
        "domain": "brookes.ac.uk",
        "subdomain_slug": "brookes",
        "display_name": "Oxford Brookes University",
        "email_domain": "brookes.ac.uk",
        "brand_color": "red",
        "brand_text_color": "white",
        "timezone": "Europe/London",
    })
    assert resp.status_code == 302
    
    cfg = UniversityConfig.query.filter_by(domain="brookes.ac.uk").first()
    assert cfg is not None
    assert cfg.display_name == "Oxford Brookes University"
    assert cfg.timezone == "Europe/London"

    # 2. Edit the config
    resp_edit = client.post("/admin/universities/brookes.ac.uk/edit", data={
        "subdomain_slug": "brookes-new",
        "display_name": "Oxford Brookes New",
        "email_domain": "brookes.ac.uk",
        "brand_color": "blue",
        "brand_text_color": "black",
        "timezone": "Asia/Dubai",
    })
    assert resp_edit.status_code == 302
    db_session.session.refresh(cfg)
    assert cfg.subdomain_slug == "brookes-new"
    assert cfg.timezone == "Asia/Dubai"

def test_admin_seasons_crud_and_activation(client, db_session):
    """Test creating, editing, and activating seasons via admin panel."""
    admin = User(
        email="admin@reuni.ac.uk",
        name="Admin User",
        role="admin",
        is_verified=True,
    )
    admin.set_password("Password123!")
    cfg = UniversityConfig(
        domain="brookes.ac.uk",
        subdomain_slug="brookes",
        display_name="Oxford Brookes University",
    )
    db_session.session.add_all([admin, cfg])
    db_session.session.commit()

    client.post("/auth/login", data={"email": "admin@reuni.ac.uk", "password": "Password123!"})

    # 1. Create a season
    resp = client.post("/admin/seasons/new", data={
        "university_domain": "brookes.ac.uk",
        "name": "Autumn 2026",
        "start_date": "2026-09-01",
        "end_date": "2026-12-15",
    })
    assert resp.status_code == 302

    season = Season.query.filter_by(name="Autumn 2026").first()
    assert season is not None
    assert season.is_active is False
    assert season.is_complete is False

    # Create another season to test deactivation of duplicates upon activation
    season2 = Season(
        university_domain="brookes.ac.uk",
        name="Winter 2026",
        start_date=datetime(2026, 12, 16),
        end_date=datetime(2027, 3, 1),
        is_active=True,
        is_complete=False,
    )
    db_session.session.add(season2)
    db_session.session.commit()

    # 2. Activate Autumn 2026
    resp_act = client.post(f"/admin/seasons/{season.id}/activate")
    assert resp_act.status_code == 302

    db_session.session.refresh(season)
    db_session.session.refresh(season2)

    assert season.is_active is True
    assert season2.is_active is False  # should be deactivated automatically

    # 3. Edit season
    resp_edit = client.post(f"/admin/seasons/{season.id}/edit", data={
        "name": "Autumn 2026 Revised",
        "start_date": "2026-09-02",
        "end_date": "2026-12-16",
    })
    assert resp_edit.status_code == 302
    db_session.session.refresh(season)
    assert season.name == "Autumn 2026 Revised"
    assert season.start_date == datetime(2026, 9, 2)
