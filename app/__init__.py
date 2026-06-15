"""
Reuni — Application Factory
"""

import os

from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user, logout_user
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Load .env file if present (for local development)
load_dotenv()

# Initialise extensions (bound to app inside create_app)
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "info"
csrf = CSRFProtect()
migrate = Migrate()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1000 per day", "1000 per hour"],
    storage_uri="memory://",
)


def create_app(config_class=None):
    """Application factory — creates and configures the Flask app."""

    app = Flask(__name__)

    # Load configuration
    if config_class is None:
        from app.config import DevelopmentConfig
        config_class = DevelopmentConfig
    app.config.from_object(config_class)

    # Run production validation if available
    if hasattr(config_class, "init_app"):
        config_class.init_app(app)

    # Ensure the instance folder exists (SQLite DB lives here)
    os.makedirs(app.instance_path, exist_ok=True)

    # Ensure the uploads folder exists
    os.makedirs(os.path.join(app.static_folder, "uploads"), exist_ok=True)

    # Security: limit upload size to 5 MB
    app.config.setdefault("MAX_CONTENT_LENGTH", 5 * 1024 * 1024)

    # Bind extensions to this app instance
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # Configure rotating file logging
    if not app.debug and not app.testing:
        import logging
        from logging.handlers import RotatingFileHandler
        log_dir = os.path.join(app.instance_path, "logs")
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "Reuni.log"),
            maxBytes=10240000,
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Reuni startup')

    # Initialize rate limiter
    limiter.init_app(app)

    # User loader for Flask-Login
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @app.before_request
    def enforce_session_rules():
        from datetime import datetime, timezone, timedelta

        # Expire session cache to ensure fresh data in concurrent/test environments
        db.session.expire_all()

        # 1. Deactivated account check — applies to all roles
        user_id = session.get("_user_id")
        if user_id:
            user = db.session.get(User, int(user_id))
            if user and not user.is_active:
                logout_user()
                flash("Your account has been deactivated. Contact support.", "danger")
                return redirect(url_for("auth.login"))

        # 2. Partner 7-day expiry check
        if current_user.is_authenticated and current_user.role == 'partner':
            logged_in_at_str = session.get('logged_in_at')
            if logged_in_at_str:
                try:
                    logged_in_at = datetime.fromisoformat(logged_in_at_str)
                    now = datetime.now(timezone.utc).replace(tzinfo=None)
                    if now - logged_in_at > timedelta(days=7):
                        logout_user()
                        flash("Your session has expired. Please log in again.", "info")
                        return redirect(url_for("auth.login"))
                except ValueError:
                    # Corrupted session payload fallback
                    logout_user()
                    return redirect(url_for("auth.login"))
            else:
                # Force logout if timestamp is missing to avoid silent skip
                logout_user()
                flash("Your session has expired. Please log in again.", "info")
                return redirect(url_for("auth.login"))

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.items import items_bp
    from app.routes.partner import partner_bp
    from app.routes.admin import admin_bp
    from app.utils.decorators import verified_required

    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(partner_bp)
    app.register_blueprint(admin_bp)

    # ── Marketplace home page (merged browse + landing) ──
    @app.route("/")
    def index():
        from app.models import Item, CATEGORIES

        active_category = request.args.get("category", "")
        search_query = request.args.get("q", "").strip()
        price_type = request.args.get("price_type", "all")
        min_price = request.args.get("min_price", "").strip()
        max_price = request.args.get("max_price", "").strip()
        active_condition = request.args.get("condition", "")
        sort_by = request.args.get("sort", "newest")

        query = Item.query.filter_by(is_sold=False)

        # Apply Category Filter
        if active_category and active_category in CATEGORIES:
            query = query.filter_by(category=active_category)

        # Apply Search Query (escaping '%' and '_')
        if search_query:
            escaped_search = search_query.replace("/", "//").replace("%", "/%").replace("_", "/_")
            query = query.filter(Item.title.ilike(f"%{escaped_search}%", escape="/"))

        # Apply Price Type Filter (All, Free, Paid)
        if price_type == "free":
            query = query.filter(Item.is_free == True)
        elif price_type == "paid":
            query = query.filter(Item.is_free == False)

        # Apply Price Range Filters (Min & Max)
        if min_price:
            try:
                query = query.filter(Item.price >= float(min_price))
            except ValueError:
                pass
        if max_price:
            try:
                query = query.filter(Item.price <= float(max_price))
            except ValueError:
                pass

        # Apply Condition Filter
        if active_condition:
            query = query.filter(Item.condition == active_condition)

        # Apply Sorting
        if sort_by == "price-low":
            order_clause = (Item.buyer_id.is_(None).desc(), Item.price.asc(), Item.created_at.desc())
        elif sort_by == "price-high":
            order_clause = (Item.buyer_id.is_(None).desc(), Item.price.desc(), Item.created_at.desc())
        elif sort_by == "eco":
            order_clause = (Item.buyer_id.is_(None).desc(), Item.kg_saved.desc(), Item.created_at.desc())
        else:
            order_clause = (Item.buyer_id.is_(None).desc(), Item.created_at.desc())

        page = request.args.get("page", 1, type=int)
        pagination = query.order_by(*order_clause).paginate(
            page=page, per_page=12, error_out=False
        )
        items = pagination.items

        return render_template(
            "index.html",
            items=items,
            pagination=pagination,
            categories=CATEGORIES,
            active_category=active_category,
            search_query=search_query,
            price_type=price_type,
            min_price=min_price,
            max_price=max_price,
            condition=active_condition,
            sort=sort_by,
        )

    @app.context_processor
    def inject_global_stats():
        from app.models import Item, User
        from app import db
        try:
            total_kg = db.session.query(db.func.sum(Item.kg_saved)).filter(Item.is_sold == True).scalar() or 0.0
            total_users = db.session.query(db.func.count(User.id)).filter(User.is_verified == True).scalar() or 0
        except Exception:
            total_kg = 0.0
            total_users = 0
        return dict(campus_total_kg=total_kg, campus_total_users=total_users)

    # ── Dashboard ──
    @app.route("/dashboard")
    @login_required
    def dashboard():
        from app.models import Item

        my_listings = (
            Item.query
            .filter_by(seller_id=current_user.id)
            .order_by(Item.created_at.desc())
            .all()
        )
        my_purchases = (
            Item.query
            .filter_by(buyer_id=current_user.id, is_sold=True)
            .order_by(Item.created_at.desc())
            .all()
        )
        my_claims = (
            Item.query
            .filter_by(buyer_id=current_user.id, is_sold=False)
            .order_by(Item.created_at.desc())
            .all()
        )

        return render_template(
            "dashboard.html",
            my_listings=my_listings,
            my_purchases=my_purchases,
            my_claims=my_claims,
        )

    @app.route("/profile")
    @login_required
    def profile():
        from app.models import Item

        total_listed = Item.query.filter_by(seller_id=current_user.id).count()
        total_sold = Item.query.filter_by(
            seller_id=current_user.id, is_sold=True
        ).count()
        total_bought = Item.query.filter_by(buyer_id=current_user.id, is_sold=True).count()
        active_listings = Item.query.filter_by(
            seller_id=current_user.id, is_sold=False, buyer_id=None
        ).all()

        return render_template(
            "profile.html",
            total_listed=total_listed,
            total_sold=total_sold,
            total_bought=total_bought,
            active_listings=active_listings,
        )
    
    # ── Settings Routes ──
    @app.route("/settings", methods=["GET"])
    @login_required
    @verified_required
    def settings():
        return render_template("settings.html")

    @app.route("/settings/phone", methods=["GET", "POST"])
    @login_required
    @verified_required
    def settings_phone():
        if request.method == "GET":
            return redirect(url_for("settings"))

        from app.routes.auth import _normalise_phone
        from app.models import User
        import re

        phone_raw = request.form.get("phone_number", "").strip()

        # No user of any role may set their phone number to None/empty once it has been set.
        if not phone_raw:
            flash("Phone number is required.", "danger")
            return redirect(url_for("settings"))

        # Normalise phone
        phone_number = _normalise_phone(phone_raw)

        # Validate format
        if not re.match(r'^\+\d{10,15}$', phone_number):
            flash("Please enter a valid phone number (e.g. +447912345678 or UK mobile).", "danger")
            return redirect(url_for("settings"))

        # If same as current:
        if phone_number == current_user.phone_number:
            flash("That's already your phone number.", "info")
            return redirect(url_for("settings"))

        # Check uniqueness against other users (both verified and unverified)
        duplicate_user = User.query.filter(User.phone_number == phone_number, User.id != current_user.id).first()
        if duplicate_user:
            flash("This number is already registered to another account.", "danger")
            return redirect(url_for("settings"))

        # Update
        current_user.phone_number = phone_number
        try:
            db.session.commit()
            flash("Phone number updated successfully.", "success")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Database error during phone update: {e}")
            flash("A database error occurred. Please try again.", "danger")

        return redirect(url_for("settings"))

    @app.route("/settings/password", methods=["GET", "POST"])
    @login_required
    @verified_required
    def settings_password():
        if request.method == "GET":
            return redirect(url_for("settings"))

        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not current_password or not new_password or not confirm_password:
            flash("All password fields are required.", "danger")
            return redirect(url_for("settings"))

        # Verify current password
        if not current_user.check_password(current_password):
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("settings"))

        # Check new == confirm
        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("settings"))

        # Check new != current
        if new_password == current_password:
            flash("New password must be different from your current password.", "danger")
            return redirect(url_for("settings"))

        # Validate complexity
        min_pw_len = app.config.get("MIN_PASSWORD_LENGTH", 8)
        if len(new_password) < min_pw_len:
            flash(f"Password must be at least {min_pw_len} characters long.", "danger")
            return redirect(url_for("settings"))

        if (not any(c.isupper() for c in new_password) or
            not any(c.islower() for c in new_password) or
            not any(c.isdigit() for c in new_password)):
            flash("Password must contain at least one uppercase letter, one lowercase letter, and one digit.", "danger")
            return redirect(url_for("settings"))

        # Update password
        current_user.set_password(new_password)
        try:
            db.session.commit()
            flash("Password updated successfully.", "success")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Database error during password update: {e}")
            flash("A database error occurred. Please try again.", "danger")

        return redirect(url_for("settings"))

    def delete_account_limit_key():
        from flask_login import current_user
        return f"delete_account:{current_user.id if current_user.is_authenticated else 'anon'}"

    @app.route("/settings/delete", methods=["POST"])
    @limiter.limit("3 per hour", key_func=delete_account_limit_key)
    @login_required
    @verified_required
    def delete_account():
        # 1. Server-Side Confirmation Check
        confirm_text = request.form.get("delete_confirm_text", "").strip()
        if confirm_text != "DELETE":
            flash("Confirmation text did not match. Account deletion aborted.", "danger")
            return redirect(url_for("settings"))

        user = current_user
        user_id = user.id

        # 2. Idempotency Guard (Prevents double submission errors)
        if user.email.startswith("deleted_") or user.deletion_pending_until is not None:
            return redirect(url_for("index"))

        # 3. Role Block Guards (Admins and partners must be offboarded via separate workflows)
        if user.role == "admin":
            flash("Administrator accounts cannot be deleted directly. Please contact system engineering for admin offboarding.", "danger")
            return redirect(url_for("settings"))
        elif user.role == "partner":
            flash("Partner accounts cannot be deleted directly. Please contact the administrator to offboard your institution.", "danger")
            return redirect(url_for("settings"))

        from app.models import Item, CancellationRecord
        from app.utils.emails import send_email
        from datetime import datetime, timezone, timedelta

        # 4. Cancel Claims with Email Notifications to Other Parties
        # Active claims where the user is the buyer:
        buyer_claims = Item.query.filter_by(buyer_id=user_id, is_sold=False).all()
        for item in buyer_claims:
            # Cancel the claim
            item.buyer_id = None
            item.pin_code = None
            item.pin_expires_at = None
            item.claimed_at = None
            item.pin_attempts = 0
            
            # Notify the seller
            try:
                seller = item.seller
                if seller and seller.email and not seller.email.endswith("@deleted.reuni"):
                    email_html = (
                        f"<p>Hello {seller.name},</p>"
                        f"<p>The claim on the item \"<strong>{item.title}</strong>\" has been cancelled "
                        f"because the buyer's account has been deactivated for deletion.</p>"
                        f"<p>The item is now available back on the marketplace.</p>"
                        f"<p>— The Reuni team</p>"
                    )
                    send_email(
                        to_email=seller.email,
                        to_name=seller.name,
                        subject=f"A claim on {item.title} has been cancelled",
                        html_content=email_html
                    )
            except Exception as mail_err:
                app.logger.warning(f"Failed to send deletion claim cancellation email to seller: {mail_err}")

        # Active claims where the user is the seller:
        seller_claims = Item.query.filter(Item.seller_id == user_id, Item.buyer_id != None, Item.is_sold == False).all()
        for item in seller_claims:
            buyer = item.buyer
            # Cancel the claim
            item.buyer_id = None
            item.pin_code = None
            item.pin_expires_at = None
            item.claimed_at = None
            item.pin_attempts = 0
            
            # Notify the buyer
            try:
                if buyer and buyer.email and not buyer.email.endswith("@deleted.reuni"):
                    email_html = (
                        f"<p>Hello {buyer.name},</p>"
                        f"<p>The claim on the item \"<strong>{item.title}</strong>\" has been cancelled "
                        f"because the seller's account has been deactivated for deletion.</p>"
                        f"<p>— The Reuni team</p>"
                    )
                    send_email(
                        to_email=buyer.email,
                        to_name=buyer.name,
                        subject=f"A claim on {item.title} has been cancelled",
                        html_content=email_html
                    )
            except Exception as mail_err:
                app.logger.warning(f"Failed to send deletion claim cancellation email to buyer: {mail_err}")

        # 5. Remove Active Listings (Unsold Items)
        active_listings = Item.query.filter_by(seller_id=user_id, is_sold=False).all()
        
        # Deletion ordering guard: read image filenames from memory before deleting row
        image_filenames_to_delete = [item.image_filename for item in active_listings if item.image_filename]
        
        for item in active_listings:
            # Delete cancellation records of unsold items
            CancellationRecord.query.filter_by(item_id=item.id).delete()
            db.session.delete(item)

        # 6. Deactivate and Queue Deletion
        user.is_active = False
        user.deletion_pending_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30)

        # 7. Log Deactivation
        app.logger.info(f"GDPR Deactivation: User {user_id} deactivated and queued for deletion on {user.deletion_pending_until}")

        try:
            db.session.commit()
            
            # Delete image files from static/uploads ONLY after successful DB transaction
            for img_filename in image_filenames_to_delete:
                img_path = os.path.join(app.static_folder, "uploads", img_filename)
                if os.path.isfile(img_path):
                    try:
                        os.remove(img_path)
                    except Exception as img_err:
                        app.logger.warning(f"Failed to delete image file {img_filename} from disk during user deletion: {img_err}")
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Database error during account deletion queue for user {user_id}: {e}")
            flash("A database error occurred. Your account could not be deleted.", "danger")
            return redirect(url_for("settings"))

        # 8. Immediate Logout & Session Clear
        logout_user()
        session.clear()
        
        flash("Your account has been deactivated and is scheduled for permanent deletion in 30 days.", "success")
        return redirect(url_for("index"))

    # ── Privacy Policy Route ──
    @app.route("/privacy", methods=["GET"])
    def privacy():
        return render_template("privacy.html")

    # ── Permanent session configuration ──
    @app.before_request
    def make_session_permanent():
        session.permanent = True

    # ── Request Entity Too Large error handler ──
    @app.errorhandler(413)
    def request_too_large(e):
        from flask import flash, redirect, url_for
        flash("Image too large. Maximum file size is 5MB.", "danger")
        return redirect(request.referrer or url_for('index'))

    # ── Custom error handlers ──
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(e, exc_info=True)
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # ── Security response headers ──
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        if not app.debug and not app.testing:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    # Create tables directly for testing (in-memory DB); otherwise use migrations
    if app.config.get("TESTING"):
        with app.app_context():
            db.create_all()

    from app.scheduler import init_scheduler
    init_scheduler(app)

    if not app.testing and not app.debug:
        with app.app_context():
            from flask_migrate import upgrade
            upgrade()

    return app

