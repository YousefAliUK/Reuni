from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from app import db
from app.models import Item, User
from app.utils.decorators import partner_required

partner_bp = Blueprint("partner", __name__, url_prefix="/partner")

@partner_bp.route("/dashboard")
@login_required
@partner_required
def partner_dashboard():
    is_global = (current_user.is_admin and not current_user.partner_university)
    
    # 1. Total Items Exchanged
    query_items = db.session.query(func.count(Item.id)).filter(Item.is_sold == True)
    if not is_global:
        query_items = query_items.filter(Item.university_domain == current_user.partner_university)
    total_items_exchanged = query_items.scalar()

    # 2. Total kg Saved
    query_kg = db.session.query(func.sum(Item.kg_saved)).filter(Item.is_sold == True)
    if not is_global:
        query_kg = query_kg.filter(Item.university_domain == current_user.partner_university)
    total_kg_saved = query_kg.scalar() or 0.0

    # 3. Total Verified Students
    query_students = db.session.query(func.count(User.id)).filter(
        User.role == 'student', 
        User.is_verified == True
    )
    if not is_global:
        query_students = query_students.filter(User.university_domain == current_user.partner_university)
    total_verified_students = query_students.scalar()

    # 4. Items by Category
    query_categories = db.session.query(
        Item.category, 
        func.count(Item.id)
    ).filter(Item.is_sold == True)
    if not is_global:
        query_categories = query_categories.filter(Item.university_domain == current_user.partner_university)
    items_by_category = query_categories.group_by(Item.category).all()

    return render_template(
        "partner/dashboard.html",
        total_items_exchanged=total_items_exchanged,
        total_kg_saved=float(total_kg_saved),
        total_verified_students=total_verified_students,
        items_by_category=items_by_category,
        is_global=is_global
    )
