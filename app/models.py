"""
Reuni — Database Models
"""

from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db
import sqlalchemy as sa


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

CONDITION_CHOICES = ["New", "Like New", "Good", "Fair", "For Parts"]

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
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    kg_saved_total = db.Column(db.Numeric(10, 2, asdecimal=False), default=0.0)
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False, server_default=sa.text('0'))
    locked_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    role = db.Column(db.String(20), nullable=False, default='student', server_default='student')
    partner_university = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False, server_default=sa.text('true'))
    deletion_pending_until = db.Column(db.DateTime, nullable=True)

    # Email ownership verification fields
    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    university_domain = db.Column(db.String(100), nullable=True)
    email_verification_code = db.Column(db.String(256), nullable=True)
    email_verification_expires_at = db.Column(db.DateTime, nullable=True)
    email_verification_attempts = db.Column(db.Integer, default=0, nullable=False)

    # Relationship
    items = db.relationship(
        "Item", foreign_keys="Item.seller_id", backref="seller", lazy=True
    )

    @property
    def is_partner(self):
        return self.role == 'partner'

    @property
    def is_admin(self):
        return self.role == 'admin'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def anonymise(self):
        """Wipes personal data from the user record according to UK GDPR."""
        self.name = "Deleted User"
        self.email = f"deleted_{self.id}@deleted.reuni"
        # Must be explicitly None (SQL NULL), not an empty string "", so that multiple
        # deleted records do not violate the phone_number unique constraint (NULL != NULL).
        self.phone_number = None
        import secrets
        self.password_hash = generate_password_hash(secrets.token_hex(32))
        self.is_verified = False
        self.is_active = False
        self.university_domain = None
        self.partner_university = None
        self.role = "student"
        self.deletion_pending_until = None
        # Zero environmental impact score (GDPR data minimisation)
        # WARNING: Zeroing this out means users.kg_saved_total will be 0.0 for deleted accounts.
        # Future features calculating global ESG stats or university-wide circular economy impact
        # MUST query and sum the items table directly (Item.kg_saved) where is_sold=True,
        # rather than summing User.kg_saved_total, to avoid undercounting deleted users' impact.
        # Sold items retain their university_domain and kg_saved by design.
        self.kg_saved_total = 0.0
        # Clear operational temporal PII logs
        self.failed_login_attempts = 0
        self.locked_until = None

    def __repr__(self):
        return f"<User {self.email}>"

# ──────────────────────────────────────────────
# Item Model
# ──────────────────────────────────────────────
class Item(db.Model):
    __tablename__ = "items"
    __table_args__ = (
        # Enforce max description length at DB level.
        # The backend also validates this in Python (items.py), so this is belt-and-suspenders.
        db.CheckConstraint('length(description) <= 2000', name='ck_items_description_length'),
    )

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    description = db.Column(db.Text, default="")
    category = db.Column(db.String(60), nullable=False)
    condition = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Numeric(10, 2, asdecimal=False), default=0.0)
    is_free = db.Column(db.Boolean, default=False)
    image_filename = db.Column(db.String(255), nullable=True, default=None)
    kg_saved = db.Column(db.Numeric(10, 2, asdecimal=False), default=0.0)
    pin_code = db.Column(db.String(256), nullable=True, default=None)
    pin_expires_at = db.Column(db.DateTime, nullable=True, default=None)
    claimed_at = db.Column(db.DateTime, nullable=True, default=None)
    pin_attempts = db.Column(db.Integer, default=0)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    is_sold = db.Column(db.Boolean, default=False)

    university_domain = db.Column(db.String(100), nullable=True)

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


# ──────────────────────────────────────────────
# Cancellation Record Model
# ──────────────────────────────────────────────
class CancellationRecord(db.Model):
    __tablename__ = "cancellation_records"

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    cancelled_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    other_party_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    claimed_at = db.Column(db.DateTime, nullable=False)
    cancelled_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    hours_held = db.Column(db.Float, nullable=False)
    tier = db.Column(db.String(10), nullable=False)  # 'clean' or 'late'
    cancelled_by_role = db.Column(db.String(10), nullable=False)  # 'buyer' or 'seller'

    # Relationships
    item = db.relationship("Item", backref=db.backref("cancellations", lazy=True))
    cancelled_by = db.relationship("User", foreign_keys=[cancelled_by_id], backref="cancellations_initiated", lazy=True)
    other_party = db.relationship("User", foreign_keys=[other_party_id], backref="cancellations_received", lazy=True)

    def __repr__(self):
        return f"<CancellationRecord item_id={self.item_id} tier={self.tier}>"
