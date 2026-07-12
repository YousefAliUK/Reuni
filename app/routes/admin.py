import re
import hashlib
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db, cache
from app.utils.emails import send_email
from app.models import User, UniversityConfig, Season
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
    
    if not re.fullmatch(r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\.)+ac\.uk", university_domain):
        flash("Please enter a valid .ac.uk university domain.", "danger")
        return redirect(url_for("admin.admin_partners"))
        
    token = generate_partner_invite_token(university_domain, current_app.config["SECRET_KEY"])
    base = current_app.config.get("BASE_URL", "").rstrip("/")
    invite_url = f"{base}{url_for('auth.invite_register', token=token)}"
    
    # Audit log entry
    current_app.logger.info(
        f"SECURITY: Partner invite generated for {university_domain} by admin id={current_user.id} at {datetime.now(timezone.utc).replace(tzinfo=None)}"
    )
    
    # Trigger background logo download job
    from app.utils.logo_downloader import start_logo_fetch_job
    start_logo_fetch_job(current_app._get_current_object(), university_domain)
    
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
    if not user or user.role != "partner":
        flash("Partner not found.", "danger")
        return redirect(url_for("admin.admin_partners"))
        
    user.is_active = False
    db.session.commit()
    current_app.logger.info(f"SECURITY: Admin id={current_user.id} deactivated partner id={user.id}")
    
    # Send deactivation notification email
    try:
        from html import escape as html_escape
        email_html = (
            f"<p>Hello {html_escape(user.name)},</p>"
            f"<p>Your Reuni partner access for <strong>{html_escape(user.partner_university or 'your university')}</strong> "
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
        import hashlib
        email_hash = hashlib.sha256(user.email.encode('utf-8')).hexdigest()[:16]
        current_app.logger.error(f"Failed to send deactivation email to email_hash={email_hash}: {e}")
        
    flash(f"Partner account {user.email} has been deactivated.", "success")
    return redirect(url_for("admin.admin_partners"))


# ─── University Configuration Management ───

@admin_bp.route("/universities", methods=["GET"])
@login_required
@admin_required
def admin_universities():
    configs = UniversityConfig.query.all()
    return render_template("admin/universities.html", configs=configs)


@admin_bp.route("/universities/new", methods=["GET", "POST"])
@login_required
@admin_required
def new_university():
    if request.method == "POST":
        domain = request.form.get("domain", "").strip().lower()
        subdomain_slug = request.form.get("subdomain_slug", "").strip().lower()
        display_name = request.form.get("display_name", "").strip()
        email_domain = request.form.get("email_domain", "").strip().lower()
        brand_color = request.form.get("brand_color", "").strip() or "var(--color-primary-muted)"
        brand_text_color = request.form.get("brand_text_color", "").strip() or "var(--color-primary)"
        timezone_str = request.form.get("timezone", "").strip() or "Europe/London"

        if not domain or not subdomain_slug or not display_name or not email_domain:
            flash("All required fields must be filled.", "danger")
            return render_template("admin/universities_form.html", config=None)

        # Check if domain or subdomain slug already exists
        existing = UniversityConfig.query.filter(
            (UniversityConfig.domain == domain) | 
            (UniversityConfig.subdomain_slug == subdomain_slug)
        ).first()
        if existing:
            flash("University domain or subdomain slug already exists.", "danger")
            return render_template("admin/universities_form.html", config=None)

        cfg = UniversityConfig(
            domain=domain,
            subdomain_slug=subdomain_slug,
            display_name=display_name,
            email_domain=email_domain,
            brand_color=brand_color,
            brand_text_color=brand_text_color,
            timezone=timezone_str,
        )
        db.session.add(cfg)
        db.session.commit()
        # Invalidate subdomain cache
        cache.delete("subdomain_map")
        flash("University configuration created successfully.", "success")
        return redirect(url_for("admin.admin_universities"))

    return render_template("admin/universities_form.html", config=None)


@admin_bp.route("/universities/<domain>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def edit_university(domain):
    cfg = UniversityConfig.query.filter_by(domain=domain).first()
    if not cfg:
        flash("University configuration not found.", "danger")
        return redirect(url_for("admin.admin_universities"))

    if request.method == "POST":
        subdomain_slug = request.form.get("subdomain_slug", "").strip().lower()
        display_name = request.form.get("display_name", "").strip()
        email_domain = request.form.get("email_domain", "").strip().lower()
        brand_color = request.form.get("brand_color", "").strip() or "var(--color-primary-muted)"
        brand_text_color = request.form.get("brand_text_color", "").strip() or "var(--color-primary)"
        timezone_str = request.form.get("timezone", "").strip() or "Europe/London"

        if not subdomain_slug or not display_name or not email_domain:
            flash("All required fields must be filled.", "danger")
            return render_template("admin/universities_form.html", config=cfg)

        # Check duplicate subdomain slug (exclude self)
        dup = UniversityConfig.query.filter(
            UniversityConfig.subdomain_slug == subdomain_slug,
            UniversityConfig.domain != domain
        ).first()
        if dup:
            flash("Subdomain slug already in use.", "danger")
            return render_template("admin/universities_form.html", config=cfg)

        cfg.subdomain_slug = subdomain_slug
        cfg.display_name = display_name
        cfg.email_domain = email_domain
        cfg.brand_color = brand_color
        cfg.brand_text_color = brand_text_color
        cfg.timezone = timezone_str

        db.session.commit()
        # Invalidate subdomain cache
        cache.delete("subdomain_map")
        flash("University configuration updated successfully.", "success")
        return redirect(url_for("admin.admin_universities"))

    return render_template("admin/universities_form.html", config=cfg)


# ─── Season Management ───

@admin_bp.route("/seasons", methods=["GET"])
@login_required
@admin_required
def admin_seasons():
    uni_domain = request.args.get("university_domain", "").strip()
    if uni_domain:
        seasons = Season.query.filter_by(university_domain=uni_domain).order_by(Season.start_date.desc()).all()
    else:
        seasons = Season.query.order_by(Season.start_date.desc()).all()
    configs = UniversityConfig.query.all()
    return render_template("admin/seasons.html", seasons=seasons, configs=configs, selected_domain=uni_domain)


@admin_bp.route("/seasons/new", methods=["POST"])
@login_required
@admin_required
def new_season():
    uni_domain = request.form.get("university_domain", "").strip()
    name = request.form.get("name", "").strip()
    start_str = request.form.get("start_date", "").strip()
    end_str = request.form.get("end_date", "").strip()

    if not uni_domain or not name or not start_str or not end_str:
        flash("All fields are required.", "danger")
        return redirect(url_for("admin.admin_seasons"))

    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_str, "%Y-%m-%d")
    except ValueError:
        flash("Invalid date format. Use YYYY-MM-DD.", "danger")
        return redirect(url_for("admin.admin_seasons"))

    if start_date >= end_date:
        flash("Start date must be before end date.", "danger")
        return redirect(url_for("admin.admin_seasons"))

    season = Season(
        university_domain=uni_domain,
        name=name,
        start_date=start_date,
        end_date=end_date,
        is_active=False,
        is_complete=False,
    )
    db.session.add(season)
    db.session.commit()
    flash("Season created successfully.", "success")
    return redirect(url_for("admin.admin_seasons"))


@admin_bp.route("/seasons/<int:season_id>/activate", methods=["POST"])
@login_required
@admin_required
def activate_season(season_id):
    # Lock the season row to start with
    season = db.session.query(Season).filter_by(id=season_id).with_for_update().first()
    if not season or season.is_complete:
        flash("Season not found or already complete.", "danger")
        return redirect(url_for("admin.admin_seasons"))

    # Lock parent UniversityConfig row to serialize activations for this university
    uni_cfg = db.session.query(UniversityConfig).filter_by(domain=season.university_domain).with_for_update().first()

    # Deactivate other active seasons for the same university domain
    active_seasons = Season.query.filter_by(
        university_domain=season.university_domain,
        is_active=True
    ).all()
    for s in active_seasons:
        s.is_active = False

    season.is_active = True
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error activating season {season_id}: {e}")
        flash("Failed to activate season due to a database error.", "danger")
        return redirect(url_for("admin.admin_seasons"))
    flash(f"Season '{season.name}' activated successfully.", "success")
    return redirect(url_for("admin.admin_seasons"))


@admin_bp.route("/seasons/<int:season_id>/edit", methods=["POST"])
@login_required
@admin_required
def edit_season(season_id):
    season = db.session.get(Season, season_id)
    if not season or season.is_complete:
        flash("Season not found or already complete.", "danger")
        return redirect(url_for("admin.admin_seasons"))

    name = request.form.get("name", "").strip()
    start_str = request.form.get("start_date", "").strip()
    end_str = request.form.get("end_date", "").strip()

    if not name or not start_str or not end_str:
        flash("All fields are required.", "danger")
        return redirect(url_for("admin.admin_seasons"))

    try:
        start_date = datetime.strptime(start_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_str, "%Y-%m-%d")
    except ValueError:
        flash("Invalid date format. Use YYYY-MM-DD.", "danger")
        return redirect(url_for("admin.admin_seasons"))

    if start_date >= end_date:
        flash("Start date must be before end date.", "danger")
        return redirect(url_for("admin.admin_seasons"))

    season.name = name
    season.start_date = start_date
    season.end_date = end_date
    db.session.commit()
    flash("Season updated successfully.", "success")
    return redirect(url_for("admin.admin_seasons"))
