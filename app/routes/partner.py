from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func
import re
from app import db
from app.models import Item, User
from app.utils.decorators import partner_required
from datetime import datetime, timezone

partner_bp = Blueprint("partner", __name__, url_prefix="/partner")

UNIVERSITY_NAMES = {
    "brookes.ac.uk": "Oxford Brookes University",
    "ox.ac.uk": "University of Oxford",
    "cam.ac.uk": "University of Cambridge",
    "lse.ac.uk": "London School of Economics",
    "ucl.ac.uk": "University College London",
    "imperial.ac.uk": "Imperial College London",
    "manchester.ac.uk": "University of Manchester",
    "ed.ac.uk": "University of Edinburgh"
}

# Per-category CO₂e conversion factors (kg CO₂e avoided per kg diverted from landfill).
# Source: WRAP / DEFRA Waste Hierarchy material-specific emission factors.
# These represent the avoided emissions from manufacturing equivalent new goods.
CO2E_FACTORS = {
    'Electronics': 40.0,  # High — semiconductor/rare earth manufacturing footprint
    'Furniture':    7.5,  # Wood/composite manufacturing
    'Clothing':     5.0,  # Textile production (cotton, synthetic)
    'Kitchenware':  3.0,  # Mixed metals/ceramics
    'Sports':       4.0,  # Mixed materials
    'Books':        1.5,  # Paper/pulp
    'Stationery':   1.0,  # Paper/lightweight materials
    'Other':        3.0,  # Conservative default
}

CATEGORY_ICONS = {
    "Furniture": "chair",
    "Kitchenware": "local_dining",
    "Electronics": "laptop_mac",
    "Sports": "sports_soccer",
    "Clothing": "checkroom",
    "Books": "book",
    "Stationery": "edit",
    "Other": "extension"
}

def get_uni_name(domain):
    """Get formal university name from domain."""
    if not domain:
        return "Global Sustainability"
    name = UNIVERSITY_NAMES.get(domain.lower())
    if not name:
        parts = domain.split('.')
        name = f"{parts[0].capitalize()} University"
    return name

def get_uni_initials(name):
    """Get initials from university name for fallback branding emblem."""
    if not name or name == "Global Sustainability":
        return "GS"
    words = [w for w in name.split() if w.lower() not in ["of", "and", "the", "for", "college", "school"]]
    if len(words) >= 2:
        return "".join(w[0] for w in words[:3]).upper()
    return name[:2].upper()

def get_relative_time(dt):
    """Convert a UTC datetime object to a relative 'time ago' string."""
    if not dt:
        return "Just now"
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    diff = now - dt
    if diff.days > 0:
        if diff.days == 1:
            return "Yesterday"
        return f"{diff.days} days ago"
    seconds = diff.seconds
    if seconds >= 3600:
        hours = seconds // 3600
        if hours == 1:
            return "1 hour ago"
        return f"{hours} hours ago"
    if seconds >= 60:
        minutes = seconds // 60
        if minutes == 1:
            return "1 minute ago"
        return f"{minutes} minutes ago"
    return "Just now"

PUBLIC_DOMAINS = {"gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com", "reuni.app", "example.com", "localhost"}


@partner_bp.route("/dashboard")
@login_required
@partner_required
def partner_dashboard():
    # Get institution domain dynamically from email if partner_university is not set (e.g. for university admins)
    user_email_domain = current_user.email.split('@')[1].lower() if current_user.email and '@' in current_user.email else None
    if user_email_domain in PUBLIC_DOMAINS:
        user_email_domain = None
        
    uni_domain = current_user.partner_university or user_email_domain
    is_global = (current_user.is_admin and not uni_domain)
    
    uni_name = get_uni_name(uni_domain) if uni_domain else "Global Sustainability"
    uni_initials = get_uni_initials(uni_name)
    
    # Single source of truth: Load logo dynamically from SVG cache
    logo_url = None
    if uni_domain and uni_domain not in PUBLIC_DOMAINS:
        from flask import current_app
        import os
        mapping = current_app.config.get("SUBDOMAIN_UNIVERSITY_MAP", {})
        reverse_map = {v: k for k, v in mapping.items()}
        slug = reverse_map.get(uni_domain, uni_domain.split('.')[0])
        
        filepath = os.path.join(current_app.static_folder, 'img', 'logos', f'{slug}.png')
        if os.path.exists(filepath):
            logo_url = f"img/logos/{slug}.png"
        else:
            from app.models import UniversityLogo
            logo_rec = UniversityLogo.query.filter_by(domain=uni_domain).first()
            if not logo_rec or logo_rec.logo_status == 'pending':
                from app.utils.logo_downloader import start_logo_fetch_job
                start_logo_fetch_job(current_app._get_current_object(), uni_domain)

    # 1. Total Items Exchanged
    query_items = db.session.query(func.count(Item.id)).filter(Item.is_sold == True)
    if not is_global:
        query_items = query_items.filter(Item.university_domain == uni_domain)
    total_items_exchanged = query_items.scalar()

    # 2. Total kg Saved
    query_kg = db.session.query(func.sum(Item.kg_saved)).filter(Item.is_sold == True)
    if not is_global:
        query_kg = query_kg.filter(Item.university_domain == uni_domain)
    total_kg_saved = query_kg.scalar() or 0.0

    # 3. Total Verified Students
    query_students = db.session.query(func.count(User.id)).filter(
        User.role == 'student', 
        User.is_verified == True
    )
    if not is_global:
        query_students = query_students.filter(User.university_domain == uni_domain)
    total_verified_students = query_students.scalar()

    # 4. Items and kg saved by Category
    query_categories = db.session.query(
        Item.category, 
        func.count(Item.id),
        func.sum(Item.kg_saved)
    ).filter(Item.is_sold == True)
    if not is_global:
        query_categories = query_categories.filter(Item.university_domain == uni_domain)
    categories_data = query_categories.group_by(Item.category).all()

    categories_list = []
    total_kg_sum = sum(float(row[2] or 0.0) for row in categories_data)
    for cat, count, kg in categories_data:
        kg_val = float(kg or 0.0)
        pct = (kg_val / total_kg_sum * 100) if total_kg_sum > 0 else 0
        categories_list.append({
            "category": cat,
            "count": count,
            "kg": kg_val,
            "percentage": pct,
            "icon": CATEGORY_ICONS.get(cat, "extension")
        })
    categories_list.sort(key=lambda x: x["kg"], reverse=True)

    # 5. Recent Completed Circular Exchanges (Live Circulation Log)
    query_recent = db.session.query(Item).filter(Item.is_sold == True)
    if not is_global:
        query_recent = query_recent.filter(Item.university_domain == uni_domain)
    recent_items = query_recent.order_by(Item.claimed_at.desc()).limit(5).all()

    recent_exchanges = []
    for item in recent_items:
        recent_exchanges.append({
            "title": item.title,
            "category": item.category,
            "kg_saved": float(item.kg_saved),
            "time_ago": get_relative_time(item.claimed_at),
            "icon": CATEGORY_ICONS.get(item.category, "extension")
        })

    # 6. CO₂e prevented — computed from categories_data using WRAP/DEFRA factors.
    #    This is separate from total_kg_saved (physical weight) and represents the
    #    estimated climate impact of the circular economy activity.
    total_co2e = round(
        sum(
            float(kg or 0.0) * CO2E_FACTORS.get(cat, 3.0)
            for cat, _count, kg in categories_data
        ),
        1
    )

    return render_template(
        "partner/dashboard.html",
        total_items_exchanged=total_items_exchanged,
        total_kg_saved=float(total_kg_saved),
        total_co2e=total_co2e,
        total_verified_students=total_verified_students,
        categories_list=categories_list,
        recent_exchanges=recent_exchanges,
        is_global=is_global,
        uni_name=uni_name,
        uni_initials=uni_initials,
        uni_domain=uni_domain,
        logo_url=logo_url
    )
