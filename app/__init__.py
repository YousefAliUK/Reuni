"""
Reuni — Application Factory
"""

import os
import secrets
import hashlib

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
    storage_uri=os.environ.get("RATELIMIT_STORAGE_URI", "memory://"),
)

from flask_caching import Cache
cache = Cache()


def get_subdomain_map():
    """
    Returns the subdomain → domain mapping, loaded from UniversityConfig table.
    Falls back to config.py hardcoded map if DB is unavailable (e.g. during migrations).
    Result is cached via Flask-Caching with a 60-second TTL to support multi-worker environments.
    """
    from flask import current_app
    cached = cache.get("subdomain_map")
    if cached is not None:
        return cached
    try:
        from app.models import UniversityConfig
        rows = UniversityConfig.query.with_entities(
            UniversityConfig.subdomain_slug, UniversityConfig.domain
        ).all()
        result = {row.subdomain_slug: row.domain for row in rows}
        if not result:
            result = current_app.config.get("SUBDOMAIN_UNIVERSITY_MAP", {})
        else:
            cache.set("subdomain_map", result, timeout=60)
    except Exception:
        result = current_app.config.get("SUBDOMAIN_UNIVERSITY_MAP", {})
    return result


def create_app(config_class=None):
    """Application factory — creates and configures the Flask app."""

    app = Flask(__name__)

    # Load configuration
    if config_class is None:
        env = os.environ.get("FLASK_ENV", "development").lower()
        if env == "production":
            from app.config import ProductionConfig
            config_class = ProductionConfig
        elif env == "testing":
            from app.config import TestingConfig
            config_class = TestingConfig
        else:
            from app.config import DevelopmentConfig
            config_class = DevelopmentConfig
    app.config.from_object(config_class)

    # Disable rate limits during local pentests if env var is True
    if os.environ.get("DISABLE_RATE_LIMITS_FOR_PENTEST") == "True" and (app.config.get("DEBUG") or app.config.get("TESTING")):
        app.config["RATELIMIT_ENABLED"] = False

    # Trust reverse proxy headers (Railway, Nginx) in non-debug/non-testing modes
    if not app.debug and not app.testing:
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

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

    # Configure Flask-Caching (SimpleCache for single-process; swap to RedisCache via CACHE_TYPE env var)
    cache_config = {
        "CACHE_TYPE": os.environ.get("CACHE_TYPE", "SimpleCache"),
        "CACHE_DEFAULT_TIMEOUT": 300,  # 5 minutes
    }
    if os.environ.get("CACHE_TYPE") == "RedisCache":
        cache_config["CACHE_REDIS_URL"] = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    app.config.from_mapping(cache_config)
    cache.init_app(app)

    # User loader for Flask-Login
    from app.models import User, Item, CancellationRecord, Message, Notification, UniversityConfig

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    if app.config.get("TESTING"):
        @app.before_request
        def expire_session_for_testing():
            db.session.expire_all()

    @app.before_request
    def detect_subdomain():
        from flask import g, abort, redirect
        
        # Skip subdomain checks for static files
        if request.endpoint == 'static':
            return
            
        from urllib.parse import urlsplit
        parsed = urlsplit(request.host_url)
        host = parsed.hostname.lower() if parsed.hostname else ""
        parts = host.split('.')
        
        base_url = app.config.get("BASE_URL") or "http://localhost:5000"
        base_parsed = urlsplit(base_url)
        base_host = base_parsed.hostname.lower() if base_parsed.hostname else ""

        subdomain = None
        if base_host and host == base_host:
            subdomain = None
        elif base_host and host.endswith("." + base_host):
            subdomain = host[: -len("." + base_host)]
        elif host.endswith(".localhost"):
            subdomain = host.split(".localhost")[0]
        elif host.endswith(".onrender.com") and len(parts) == 3:
            # Primary service root on Render (e.g. reuni.onrender.com)
            subdomain = None
        elif len(parts) >= 3:
            subdomain = parts[0]
            
        uni_map = get_subdomain_map()
        if subdomain and subdomain != 'www':
            if subdomain not in uni_map:
                # Early rejection for unrecognized subdomains
                abort(404)
            g.current_uni_domain = uni_map[subdomain]
        else:
            if app.testing and request.headers.get("X-Test-Landing") != "true":
                g.current_uni_domain = "university.ac.uk"
            else:
                g.current_uni_domain = None

        # Redirect logged-in users to their own subdomain for account-scoped pages
        if not app.testing and current_user.is_authenticated:
            if current_user.university_domain and g.current_uni_domain != current_user.university_domain:
                # Blueprints and endpoints that must belong to the user's university
                if (request.blueprint in ['partner', 'admin', 'leaderboard', 'items', 'messaging'] or 
                    request.endpoint in ['dashboard', 'profile', 'settings', 'enforce_session_rules']):
                    
                    rev_map = {v: k for k, v in uni_map.items()}
                    correct_subdomain = rev_map.get(current_user.university_domain)
                    if correct_subdomain:
                        if host == "localhost" or host.endswith(".localhost"):
                            base_domain = "localhost"
                        elif host.endswith(".onrender.com"):
                            # Render hobby/single-service does not support wildcards on *.onrender.com
                            base_domain = None
                        else:
                            base_domain = '.'.join(parts[-2:]) if len(parts) >= 2 else host
                        if base_domain:
                            port = parsed.port
                            new_host = f"{correct_subdomain}.{base_domain}"
                            if port:
                                new_host = f"{new_host}:{port}"
                            return redirect(f"{request.scheme}://{new_host}{request.full_path}")

    @app.before_request
    def enforce_session_rules():
        from datetime import datetime, timezone, timedelta
        
        # 1. Deactivated account check — applies to all roles
        user_id = session.get("_user_id")
        if user_id:
        
            # Fresh query to get current account status, only fetch the user we need
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
                    # Strip tzinfo defensively — stored as naive UTC but guard against
                    # any future change that adds timezone info to the isoformat string.
                    if logged_in_at.tzinfo is not None:
                        logged_in_at = logged_in_at.replace(tzinfo=None)
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
                # Legacy session from before the logged_in_at feature was introduced.
                # Initialize the timestamp to the current time so they get a 7-day grace period
                # starting now, rather than bypassing the security check indefinitely.
                session['logged_in_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.items import items_bp
    from app.routes.partner import partner_bp
    from app.routes.admin import admin_bp
    from app.routes.messaging import messaging_bp
    from app.routes.leaderboard import leaderboard_bp
    from app.utils.decorators import verified_required

    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)
    app.register_blueprint(partner_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(messaging_bp)
    app.register_blueprint(leaderboard_bp)



    # ── Marketplace home page (merged browse + landing) ──
    @app.route("/")
    def index():
        from flask import g
        from app.models import Item, CATEGORIES

        if g.current_uni_domain is None:
            # Logged-in User Subdomain Redirect Check
            from flask_login import current_user
            selected_uni = None
            if current_user.is_authenticated and current_user.university_domain:
                uni_map = get_subdomain_map()
                rev_map = {v: k for k, v in uni_map.items()}
                selected_uni = rev_map.get(current_user.university_domain)

            if not selected_uni:
                selected_uni = request.cookies.get("selected_uni")

            if selected_uni and not request.args.get("noredirect"):
                uni_map = get_subdomain_map()
                if selected_uni in uni_map:
                    # Redirect to subdomain
                    from urllib.parse import urlsplit
                    parsed = urlsplit(request.host_url)
                    host = parsed.hostname.lower() if parsed.hostname else ""
                    parts = host.split('.')
                    if host == "localhost" or host.endswith(".localhost"):
                        base_domain = "localhost"
                    else:
                        base_domain = '.'.join(parts[-2:]) if len(parts) >= 2 else host
                    port = parsed.port
                    new_host = f"{selected_uni}.{base_domain}"
                    if port:
                        new_host = f"{new_host}:{port}"
                    return redirect(f"{request.scheme}://{new_host}/")
            
            # Fetch aggregates for landing page
            landing_stats = cache.get("landing_stats")
            if landing_stats is None:
                from app.models import Item, User, UniversityConfig
                configs = UniversityConfig.query.all()
                universities = []
                def calculate_initials(name):
                    words = [w for w in name.split() if w.lower() not in ["university", "of", "and", "the"]]
                    if len(words) >= 2:
                        return (words[0][0] + words[1][0]).upper()
                    elif len(words) == 1:
                        return words[0][:2].upper()
                    return name[:2].upper()

                if not configs:
                    fallback_map = get_subdomain_map()
                    for slug, domain in fallback_map.items():
                        from app.routes.partner import get_uni_name
                        name = get_uni_name(domain)
                        active_count = Item.query.filter_by(
                            is_sold=False, buyer_id=None, is_deleted=False, university_domain=domain
                        ).count()
                        kg_saved = db.session.query(db.func.sum(Item.kg_saved)).filter(
                            Item.is_sold == True, Item.university_domain == domain
                        ).scalar() or 0.0
                        students = User.query.filter_by(
                            university_domain=domain, is_verified=True
                        ).count()
                        circulated = Item.query.filter(Item.university_domain == domain, Item.is_deleted == False).count()
                        universities.append({
                            "slug": slug,
                            "domain": domain,
                            "name": name,
                            "initials": calculate_initials(name),
                            "active_count": active_count,
                            "kg_saved": float(kg_saved),
                            "students": students,
                            "circulated": circulated,
                        })
                else:
                    for cfg in configs:
                        active_count = Item.query.filter_by(
                            is_sold=False, buyer_id=None, is_deleted=False, university_domain=cfg.domain
                        ).count()
                        kg_saved = db.session.query(db.func.sum(Item.kg_saved)).filter(
                            Item.is_sold == True, Item.university_domain == cfg.domain
                        ).scalar() or 0.0
                        students = User.query.filter_by(
                            university_domain=cfg.domain, is_verified=True
                        ).count()
                        circulated = Item.query.filter(Item.university_domain == cfg.domain, Item.is_deleted == False).count()
                        name = cfg.short_name or cfg.display_name
                        universities.append({
                            "slug": cfg.subdomain_slug,
                            "domain": cfg.domain,
                            "name": cfg.display_name,
                            "initials": calculate_initials(name),
                            "active_count": active_count,
                            "kg_saved": float(kg_saved),
                            "students": students,
                            "circulated": circulated,
                        })

                total_saved = db.session.query(db.func.sum(Item.kg_saved)).filter(
                    Item.is_sold == True
                ).scalar() or 0.0

                landing_stats = {
                    "total_saved": float(total_saved),
                    "total_co2": float(total_saved) * 2.5,
                    "universities": universities,
                }
                cache.set("landing_stats", landing_stats, timeout=300)

            # Resolve showcase university dynamically (defaults to Brookes, falls back to first available config)
            uni_stats = {u["domain"]: u for u in landing_stats["universities"]}
            showcase = uni_stats.get("brookes.ac.uk")
            if not showcase and landing_stats["universities"]:
                showcase = landing_stats["universities"][0]
            if not showcase:
                showcase = {
                    "name": "Oxford Brookes University",
                    "kg_saved": 0.0,
                    "active_count": 0,
                    "circulated": 0,
                    "students": 0
                }

            return render_template(
                "landing.html",
                total_saved_kg=landing_stats["total_saved"],
                total_co2_saved=landing_stats["total_co2"],
                showcase_name=showcase["name"],
                showcase_saved_kg=showcase["kg_saved"],
                showcase_circulated=showcase["circulated"],
                showcase_students=showcase["students"],
                universities=landing_stats["universities"]
            )

        active_category = request.args.get("category", "")
        search_query = request.args.get("q", "").strip()
        price_type = request.args.get("price_type", "all")
        min_price = request.args.get("min_price", "").strip()
        max_price = request.args.get("max_price", "").strip()
        active_condition = request.args.get("condition", "")
        sort_by = request.args.get("sort", "newest")

        if app.testing:
            from sqlalchemy import or_
            query = Item.query.filter(
                Item.is_sold == False,
                Item.is_deleted == False,
                or_(Item.university_domain == g.current_uni_domain, Item.university_domain.is_(None))
            )
        else:
            query = Item.query.filter_by(is_sold=False, is_deleted=False, university_domain=g.current_uni_domain)

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
        if price_type != "free":
            if min_price:
                try:
                    val = float(min_price)
                    import math
                    if math.isnan(val) or math.isinf(val):
                        raise ValueError
                    query = query.filter(Item.price >= val)
                except ValueError:
                    pass
            if max_price:
                try:
                    val = float(max_price)
                    import math
                    if math.isnan(val) or math.isinf(val):
                        raise ValueError
                    query = query.filter(Item.price <= val)
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
        from flask import g

        current_uni_domain = getattr(g, "current_uni_domain", None)
        domain_key = current_uni_domain or "global"
        cache_key = f"global_stats_{domain_key}"
        stats_data = cache.get(cache_key)
        if stats_data is not None:
            return stats_data

        # Cache miss, fetch database
        try:
            total_kg = db.session.query(db.func.sum(Item.kg_saved)).filter(Item.is_sold == True).scalar() or 0.0
            total_users = db.session.query(db.func.count(User.id)).filter(User.is_verified == True).scalar() or 0
            if current_uni_domain:
                sub_kg = db.session.query(db.func.sum(Item.kg_saved)).filter(
                    Item.is_sold == True, Item.university_domain == current_uni_domain
                ).scalar() or 0.0
                sub_users = db.session.query(db.func.count(User.id)).filter(
                    User.is_verified == True, User.university_domain == current_uni_domain
                ).scalar() or 0
            else:
                sub_kg = 0.0
                sub_users = 0
        except Exception:
            total_kg = 0.0
            total_users = 0
            sub_kg = 0.0
            sub_users = 0

        stats_data = dict(
            campus_total_kg=total_kg,
            campus_total_users=total_users,
            subdomain_total_kg=sub_kg,
            subdomain_total_users=sub_users
        )

        cache.set(cache_key, stats_data, timeout=300)
        return stats_data

    # ── Dashboard ──
    @app.route("/dashboard")
    @login_required
    def dashboard():
        from app.models import Item

        my_listings = (
            Item.query
            .filter_by(seller_id=current_user.id, is_deleted=False)
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
            .filter_by(buyer_id=current_user.id, is_sold=False, is_deleted=False)
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

        total_listed = Item.query.filter_by(seller_id=current_user.id, is_deleted=False).count()
        total_sold = Item.query.filter_by(
            seller_id=current_user.id, is_sold=True
        ).count()
        total_bought = Item.query.filter_by(buyer_id=current_user.id, is_sold=True).count()
        active_listings = Item.query.filter_by(
            seller_id=current_user.id, is_sold=False, buyer_id=None, is_deleted=False
        ).all()

        return render_template(
            "profile.html",
            total_listed=total_listed,
            total_sold=total_sold,
            total_bought=total_bought,
            active_listings=active_listings,
        )
    
    # ── Settings Routes ──
    @app.route("/settings", methods=["GET", "POST"])
    @login_required
    @verified_required
    def settings():
        if request.method == "POST":
            show_on_leaderboard = request.form.get("show_on_leaderboard") == "on"
            current_user.show_on_leaderboard = show_on_leaderboard
            db.session.commit()
            flash("Privacy settings updated successfully.", "success")
            return redirect(url_for("settings"))
        return render_template("settings.html")



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
        max_pw_len = app.config.get("MAX_PASSWORD_LENGTH", 128)
        if len(new_password) < min_pw_len:
            flash(f"Password must be at least {min_pw_len} characters long.", "danger")
            return redirect(url_for("settings"))

        if len(new_password) > max_pw_len:
            flash(f"Password must be {max_pw_len} characters or fewer.", "danger")
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
            app.logger.info(f"SECURITY: Password changed for user {current_user.id}")
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

        from html import escape as html_escape
        from app.models import Item, CancellationRecord
        from app.utils.emails import send_email
        from datetime import datetime, timezone, timedelta

        # 4. Cancel Claims with Email Notifications to Other Parties
        emails_to_send = []
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
            seller = item.seller
            if seller and seller.email and not seller.email.endswith("@deleted.reuni"):
                email_html = (
                    f"<p>Hello {html_escape(seller.name)},</p>"
                    f"<p>The claim on the item \"<strong>{html_escape(item.title)}</strong>\" has been cancelled "
                    f"because the buyer's account has been deactivated for deletion.</p>"
                    f"<p>The item is now available back on the marketplace.</p>"
                    f"<p>— The Reuni team</p>"
                )
                emails_to_send.append({
                    "to_email": seller.email,
                    "to_name": seller.name,
                    "subject": f"A claim on {item.title} has been cancelled",
                    "html_content": email_html
                })

        # Active claims where the user is the seller:
        seller_claims = Item.query.filter(Item.seller_id == user_id, Item.buyer_id.is_not(None), Item.is_sold == False).all()
        for item in seller_claims:
            buyer = item.buyer
            # Cancel the claim
            item.buyer_id = None
            item.pin_code = None
            item.pin_expires_at = None
            item.claimed_at = None
            item.pin_attempts = 0
            
            # Notify the buyer
            if buyer and buyer.email and not buyer.email.endswith("@deleted.reuni"):
                email_html = (
                    f"<p>Hello {html_escape(buyer.name)},</p>"
                    f"<p>The claim on the item \"<strong>{html_escape(item.title)}</strong>\" has been cancelled "
                    f"because the seller's account has been deactivated for deletion.</p>"
                    f"<p>— The Reuni team</p>"
                )
                emails_to_send.append({
                    "to_email": buyer.email,
                    "to_name": buyer.name,
                    "subject": f"A claim on {item.title} has been cancelled",
                    "html_content": email_html
                })

        # 5. Soft-delete Active Listings (Unsold Items)
        active_listings = Item.query.filter_by(seller_id=user_id, is_sold=False).all()
        
        # Deletion ordering guard: read image filenames from memory before deleting row
        image_filenames_to_delete = [item.image_filename for item in active_listings if item.image_filename]
        
        for item in active_listings:
            item.is_deleted = True
            item.image_filename = None

        # 6. Deactivate and Queue Deletion
        user.is_active = False
        user.deletion_pending_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=30)

        # 7. Log Deactivation
        app.logger.info(f"GDPR Deactivation: User {user_id} deactivated and queued for deletion on {user.deletion_pending_until}")

        try:
            db.session.commit()
            
            # Send emails ONLY after successful DB transaction
            for mail in emails_to_send:
                try:
                    send_email(
                        to_email=mail["to_email"],
                        to_name=mail["to_name"],
                        subject=mail["subject"],
                        html_content=mail["html_content"]
                    )
                except Exception as mail_err:
                    app.logger.warning(f"Failed to send deletion claim cancellation email: {mail_err}")

            # Delete image files ONLY after successful DB transaction
            from app.routes.items import _delete_image
            for img_filename in image_filenames_to_delete:
                try:
                    _delete_image(img_filename)
                except Exception as img_err:
                    app.logger.warning(f"Failed to delete image file {img_filename} during user deletion: {img_err}")
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

    @app.before_request
    def generate_csp_nonce():
        request.csp_nonce = secrets.token_urlsafe(32)

    @app.context_processor
    def inject_csp_nonce():
        return {"csp_nonce": getattr(request, "csp_nonce", "")}

    @app.context_processor
    def inject_turnstile_sitekey():
        return {
            "turnstile_sitekey": app.config.get("TURNSTILE_SITE_KEY") or "1x00000000000000000000AA"
        }

    @app.context_processor
    def inject_logo_helpers():
        from app.routes.partner import get_uni_name, get_uni_initials
        def get_logo_status(domain):
            # 1. Determine local file existence
            mapping = get_subdomain_map()
            reverse_map = {v: k for k, v in mapping.items()}
            slug = reverse_map.get(domain, domain.split('.')[0])
            
            for ext in ('png', 'svg'):
                filepath = os.path.join(app.static_folder, 'img', 'logos', f'{slug}.{ext}')
                if os.path.exists(filepath):
                    return 'fetched'
                
            # 2. Check database status
            from app.models import UniversityConfig
            logo_rec = UniversityConfig.query.filter_by(domain=domain).first()
            if logo_rec:
                if logo_rec.logo_status == 'no_logo':
                    return 'no_logo'
                return logo_rec.logo_status
                
            # 3. If unknown, trigger background fetch
            from app.utils.logo_downloader import start_logo_fetch_job
            start_logo_fetch_job(app, domain)
            return 'pending'
            
        def get_brand_color(domain):
            if not domain:
                return "var(--color-primary-muted)"
            from app.models import UniversityConfig
            config = UniversityConfig.query.filter_by(domain=domain).first()
            return config.brand_color if config else "var(--color-primary-muted)"
            
        def get_brand_text_color(domain):
            if not domain:
                return "var(--color-primary)"
            from app.models import UniversityConfig
            config = UniversityConfig.query.filter_by(domain=domain).first()
            return config.brand_text_color if config else "var(--color-primary)"
            
        def get_logo_url(domain):
            if not domain:
                return ""
            mapping = get_subdomain_map()
            reverse_map = {v: k for k, v in mapping.items()}
            slug = reverse_map.get(domain, domain.split('.')[0])
            
            for ext in ['png', 'svg']:
                filepath = os.path.join(app.static_folder, 'img', 'logos', f'{slug}.{ext}')
                if os.path.exists(filepath):
                    return url_for('static', filename=f'img/logos/{slug}.{ext}')
            return url_for('static', filename=f'img/logos/{slug}.png')
            
        return dict(
            get_logo_status=get_logo_status,
            get_brand_color=get_brand_color,
            get_brand_text_color=get_brand_text_color,
            get_logo_url=get_logo_url,
            get_uni_name=get_uni_name,
            get_uni_initials=get_uni_initials
        )

    # ── Request Entity Too Large error handler ──
    @app.errorhandler(413)
    def request_too_large(e):
        from flask import flash, redirect, url_for
        flash("Image too large. Maximum file size is 5MB.", "danger")
        # Validate request.referrer is same-origin to prevent open redirects
        referrer = request.referrer
        if referrer:
            from urllib.parse import urlparse
            parsed = urlparse(referrer)
            if parsed.netloc and parsed.netloc != request.host:
                referrer = None
        return redirect(referrer or url_for('index'))

    # ── Custom error handlers ──
    @app.errorhandler(400)
    def bad_request(e):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json or "application/json" in request.accept_mimetypes:
            return {"success": False, "error": "Bad Request"}, 400
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden(e):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json or "application/json" in request.accept_mimetypes:
            return {"success": False, "error": "Forbidden"}, 403
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json or "application/json" in request.accept_mimetypes:
            return {"success": False, "error": "Not Found"}, 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json or "application/json" in request.accept_mimetypes:
            return {"success": False, "error": "Method Not Allowed"}, 405
        return render_template('errors/405.html'), 405

    @app.errorhandler(429)
    def too_many_requests(e):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json or "application/json" in request.accept_mimetypes:
            return {"success": False, "error": "Too many requests. Please try again later."}, 429
        return render_template('errors/429.html'), 429

    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(e, exc_info=True)
        db.session.rollback()
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json or "application/json" in request.accept_mimetypes:
            return {"success": False, "error": "An internal server error occurred"}, 500
        return render_template('errors/500.html'), 500

    # ── Security response headers ──
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        nonce = getattr(request, 'csp_nonce', '')
        r2_url = app.config.get("CF_R2_PUBLIC_URL")
        img_src_directive = "img-src 'self' data:"
        if r2_url:
            img_src_directive += f" {r2_url}"

        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            f"script-src 'self' https://challenges.cloudflare.com https://static.cloudflareinsights.com 'nonce-{nonce}'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            f"{img_src_directive}; "
            "connect-src 'self' https://challenges.cloudflare.com https://static.cloudflareinsights.com; "
            "frame-src 'self' https://challenges.cloudflare.com; "
            "frame-ancestors 'none'"
        )
        if not app.debug and not app.testing:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # Caching optimization: cache static assets heavily at Cloudflare Edge but check frequently in the browser.
        # Disable Back-Forward Cache (bfcache) globally for dynamic HTML pages.
        if request.path.startswith('/static/'):
            response.headers["Cache-Control"] = "public, max-age=3600, s-maxage=604800"
        elif response.mimetype == "text/html":
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response

    # Create tables directly for testing (in-memory DB); otherwise use migrations
    if app.config.get("TESTING"):
        with app.app_context():
            db.create_all()

    from app.scheduler import init_scheduler
    init_scheduler(app)

    # CLI command registration for external cron triggers
    @app.cli.command("anonymise-expired-accounts")
    def anonymise_expired_accounts_command():
        """CLI command to trigger GDPR nightly deactivation anonymisation."""
        from app.scheduler import anonymise_expired_accounts
        from flask import current_app
        current_app.logger.info("Starting CLI anonymise-expired-accounts task...")
        anonymise_expired_accounts(current_app)
        current_app.logger.info("CLI anonymise-expired-accounts task completed successfully.")

    # NOTE: Migrations must be run manually as a separate deploy step:
    # $ flask db upgrade
    # Do NOT run upgrade() here — it is unsafe in production with multiple
    # Gunicorn workers (race conditions, blocking startup, no rollback path).

    return app

