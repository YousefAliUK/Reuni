"""
UniCycle — Application Factory
"""

import os

from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
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


def create_app(config_class=None):
    """Application factory — creates and configures the Flask app."""

    app = Flask(__name__)

    # Load configuration
    if config_class is None:
        from app.config import DevelopmentConfig
        config_class = DevelopmentConfig
    app.config.from_object(config_class)

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

    # User loader for Flask-Login
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.items import items_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(items_bp)

    # ── Marketplace home page (merged browse + landing) ──
    @app.route("/")
    def index():
        from app.models import Item, CATEGORIES

        active_category = request.args.get("category", "")
        search_query = request.args.get("q", "").strip()
        price_type = request.args.get("price_type", "all")
        min_price = request.args.get("min_price", "").strip()
        max_price = request.args.get("max_price", "").strip()

        query = Item.query.filter_by(is_sold=False)

        # Apply Category Filter
        if active_category and active_category in CATEGORIES:
            query = query.filter_by(category=active_category)

        # Apply Search Query
        if search_query:
            query = query.filter(Item.title.ilike(f"%{search_query}%"))

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

        items = query.order_by(Item.created_at.desc()).all()

        return render_template(
            "index.html",
            items=items,
            categories=CATEGORIES,
            active_category=active_category,
            search_query=search_query,
            price_type=price_type,
            min_price=min_price,
            max_price=max_price,
        )

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
            .filter_by(buyer_id=current_user.id)
            .order_by(Item.created_at.desc())
            .all()
        )

        return render_template(
            "dashboard.html",
            my_listings=my_listings,
            my_purchases=my_purchases,
        )

    # ── Security response headers ──
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # Create tables directly for testing (in-memory DB); otherwise use migrations
    if app.config.get("TESTING"):
        with app.app_context():
            db.create_all()

    return app
