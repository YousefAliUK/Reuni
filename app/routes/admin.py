import re
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db
from app.utils.emails import send_email
from app.models import User
from app.utils.decorators import admin_required
from app.utils.tokens import generate_partner_invite_token

from app.utils.email_validation import extract_university_domain

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.route("/partners", methods=["GET"])
@login_required
@admin_required
def admin_partners():
    partners = User.query.filter(User.role == "partner").all()
    return render_template("admin/partners.html", partners=partners)

@admin_bp.route("/partners/invite", methods=["POST"])
@login_required
@admin_required
def generate_invite():
    university_domain = request.form.get("university_domain", "").strip().lower()
    
    # If a full email address was entered, extract the domain portion
    if "@" in university_domain:
        extracted = extract_university_domain(university_domain)
        if extracted:
            university_domain = extracted
    
    if not re.match(r"^[a-zA-Z0-9.-]+\.ac\.uk$", university_domain):
        flash("Please enter a valid .ac.uk university domain.", "danger")
        return redirect(url_for("admin.admin_partners"))
        
    token = generate_partner_invite_token(university_domain, current_app.config["SECRET_KEY"])
    invite_url = url_for("auth.invite_register", token=token, _external=True)
    
    # Audit log entry
    current_app.logger.info(
        f"Partner invite generated for {university_domain} by admin {current_user.email} at {datetime.now(timezone.utc).replace(tzinfo=None)}"
    )
    
    # Render with the generated URL (flashing it is easy, but we will pass it back to the template)
    partners = User.query.filter(User.role == "partner").all()
    return render_template("admin/partners.html", partners=partners, invite_url=invite_url, university_domain=university_domain)

@admin_bp.route("/partners/<int:user_id>/deactivate", methods=["POST"])
@login_required
@admin_required
def deactivate_partner(user_id):
    if user_id == current_user.id:
        flash("You cannot deactivate your own account.", "danger")
        return redirect(url_for("admin.admin_partners"))
        
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("admin.admin_partners"))
        
    user.is_active = False
    db.session.commit()
    
    # Send deactivation notification email
    try:
        email_html = (
            f"<p>Hello {user.name},</p>"
            f"<p>Your Reuni partner access for <strong>{user.partner_university or 'your university'}</strong> "
            f"has been deactivated.</p>"
            f"<p>Contact support if this is unexpected.</p>"
            f"<p>— The Reuni team</p>"
        )
        send_email(
            to_email=user.email,
            to_name=user.name,
            subject="Reuni Account Deactivation",
            html_content=email_html
        )
    except Exception as e:
        current_app.logger.error(f"Failed to send deactivation email to {user.email}: {e}")
        
    flash(f"Partner account {user.email} has been deactivated.", "success")
    return redirect(url_for("admin.admin_partners"))
