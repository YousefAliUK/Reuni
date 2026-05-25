"""
UniCycle — Database Models
"""

from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db

# ──────────────────────────────────────────────
# Category Weights Mapping  (Category → Weight)
# Adjust values as the team sees fit.
# ──────────────────────────────────────────────
CATEGORY_WEIGHTS = {
    "Furniture": 12.0,
    "Kitchenware": 4.0,
    "Electronics": 3.0,
    "Sports": 2.5,
    "Clothing": 1.5,
    "Books": 0.8,
    "Stationery": 0.3,
    "Other": 1.0,
}

CATEGORIES = list(CATEGORY_WEIGHTS.keys())

CONDITION_CHOICES = ["New", "Like New", "Good", "Fair", "Poor"]

# Allowed image extensions for upload validation
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

# Maximum image dimension (width or height) after resize
MAX_IMAGE_SIZE = 800

# ──────────────────────────────────────────────
# User Model
# ──────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    name = db.Column(db.String(80), nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    kg_saved_total = db.Column(db.Float, default=0.0)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    # Relationship
    items = db.relationship(
        "Item", foreign_keys="Item.seller_id", backref="seller", lazy=True
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"

# ──────────────────────────────────────────────
# Item Model
# ──────────────────────────────────────────────
class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, default="")
    category = db.Column(db.String(60), nullable=False)
    condition = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, default=0.0)
    is_free = db.Column(db.Boolean, default=False)
    image_filename = db.Column(db.String(255), nullable=True, default=None)
    kg_saved = db.Column(db.Float, default=0.0)
    pin_code = db.Column(db.String(4), nullable=True, default=None)
    pin_expires_at = db.Column(db.DateTime, nullable=True, default=None)
    claimed_at = db.Column(db.DateTime, nullable=True, default=None)
    pin_attempts = db.Column(db.Integer, default=0)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    is_sold = db.Column(db.Boolean, default=False)

    # Foreign keys
    seller_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )
    buyer_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True, default=None
    )

    # Relationships
    buyer = db.relationship(
        "User", foreign_keys=[buyer_id], backref="purchases", lazy=True
    )

    def __repr__(self):
        return f"<Item {self.title}>"
