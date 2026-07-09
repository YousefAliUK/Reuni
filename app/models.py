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

ECO_TITLES = [
    "Zero Waste Hero", "Carbon Crusher", "Green Champion", "Eco Warrior",
    "Circular Pioneer", "Planet Protector", "Waste Buster",
    "Sustainability Star", "Reuse Legend", "Eco Guardian",
]

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
    last_seen_at = db.Column(db.DateTime, nullable=True)
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
    show_on_leaderboard = db.Column(db.Boolean, default=True, nullable=False, server_default=sa.text('true'))

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
        # GDPR message content anonymisation: replace message content with a placeholder
        Message.query.filter_by(sender_id=self.id).update({Message.content: "[Message removed — account deleted]"})
        # Delete notifications for this user
        Notification.query.filter_by(user_id=self.id).delete()
        import secrets
        self.password_hash = generate_password_hash(secrets.token_hex(32))
        self.is_verified = False
        self.email_verification_code = None
        self.email_verification_expires_at = None
        self.email_verification_attempts = 0
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

        # Sever and mask leaderboard snapshot entries (GDPR: preserve history, erase identity)
        # Assign a deterministic eco-title based on the rank position.
        weekly_entries = WeeklySnapshot.query.filter_by(user_id=self.id).all()
        for entry in weekly_entries:
            title_base = ECO_TITLES[entry.rank - 1] if entry.rank <= len(ECO_TITLES) else "Eco Hero"
            entry.display_name = f"{title_base} #{entry.rank}"
            entry.user_id = None

        seasonal_entries = SeasonalSnapshot.query.filter_by(user_id=self.id).all()
        for entry in seasonal_entries:
            title_base = ECO_TITLES[entry.rank - 1] if entry.rank <= len(ECO_TITLES) else "Eco Hero"
            entry.display_name = f"{title_base} #{entry.rank}"
            entry.user_id = None

    def __repr__(self):
        return f"<User id={self.id}>"

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
    pin_code = db.Column(db.String(4), nullable=True, default=None)
    pin_expires_at = db.Column(db.DateTime, nullable=True, default=None)
    claimed_at = db.Column(db.DateTime, nullable=True, default=None)
    pin_attempts = db.Column(db.Integer, default=0)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    is_sold = db.Column(db.Boolean, default=False)
    sold_at = db.Column(db.DateTime, nullable=True, default=None)

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

    @property
    def image_url(self):
        """Return the URL to access the item's image."""
        if not self.image_filename:
            return None
        
        from flask import current_app, url_for
        
        storage_provider = current_app.config.get("STORAGE_PROVIDER", "local")
        
        if storage_provider == "r2":
            r2_public_url = current_app.config.get("CF_R2_PUBLIC_URL", "").rstrip("/")
            return f"{r2_public_url}/{self.image_filename}"
                
        return url_for("static", filename=f"uploads/{self.image_filename}")

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


# ──────────────────────────────────────────────
# Message Model
# ──────────────────────────────────────────────
class Message(db.Model):
    __tablename__ = "messages"
    __table_args__ = (
        db.CheckConstraint('length(content) <= 1000', name='ck_messages_content_length'),
        db.Index('ix_messages_item_recipient', 'item_id', 'recipient_id'),
    )

    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey("items.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    item = db.relationship("Item", backref=db.backref("messages", lazy=True))
    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_messages", lazy=True)
    recipient = db.relationship("User", foreign_keys=[recipient_id], backref="received_messages", lazy=True)

    def __repr__(self):
        return f"<Message {self.id} sender={self.sender_id} recipient={self.recipient_id}>"


# ──────────────────────────────────────────────
# Notification Model
# ──────────────────────────────────────────────
class Notification(db.Model):
    __tablename__ = "notifications"
    __table_args__ = (
        db.Index('ix_notifications_user_unread', 'user_id', 'is_read'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=True)
    link = db.Column(db.String(500), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", backref=db.backref("notifications", lazy=True))

    def __repr__(self):
        return f"<Notification id={self.id} user={self.user_id}>"


# ──────────────────────────────────────────────
# University Configuration Model
# (Replaces UniversityLogo — single source of truth for all university data)
# ──────────────────────────────────────────────
class UniversityConfig(db.Model):
    __tablename__ = "university_configs"

    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(100), unique=True, nullable=False, index=True)
    subdomain_slug = db.Column(db.String(50), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(200), nullable=False)
    email_domain = db.Column(db.String(100), nullable=False)  # e.g. "brookes.ac.uk"
    timezone = db.Column(db.String(50), nullable=False, default="Europe/London")
    brand_color = db.Column(db.String(7), nullable=False, default="#1a1a2e")
    brand_text_color = db.Column(db.String(7), nullable=False, default="#ffffff")

    # Term dates (naive UTC stored; displayed/calculated in university timezone)
    autumn_term_start = db.Column(db.DateTime, nullable=True)
    autumn_term_end = db.Column(db.DateTime, nullable=True)
    spring_term_start = db.Column(db.DateTime, nullable=True)
    spring_term_end = db.Column(db.DateTime, nullable=True)
    summer_term_start = db.Column(db.DateTime, nullable=True)  # nullable — not all unis have summer term
    summer_term_end = db.Column(db.DateTime, nullable=True)

    # Logo fetching status (absorbed from UniversityLogo)
    logo_status = db.Column(db.String(20), nullable=False, default="pending")  # 'pending', 'fetched', 'no_logo'
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    seasons = db.relationship("Season", backref="university", lazy=True)
    weekly_snapshots = db.relationship(
        "WeeklySnapshot",
        foreign_keys="WeeklySnapshot.university_domain",
        primaryjoin="UniversityConfig.domain == WeeklySnapshot.university_domain",
        backref="university_config",
        lazy=True,
    )

    def __repr__(self):
        return f"<UniversityConfig domain={self.domain}>"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.subdomain_slug and self.domain:
            self.subdomain_slug = self.domain.split('.')[0]
        if not self.display_name and self.subdomain_slug:
            self.display_name = self.subdomain_slug.title()
        if not self.email_domain and self.domain:
            self.email_domain = self.domain


# ──────────────────────────────────────────────
# Season Model
# ──────────────────────────────────────────────
class Season(db.Model):
    __tablename__ = "seasons"

    id = db.Column(db.Integer, primary_key=True)
    university_domain = db.Column(
        db.String(100), db.ForeignKey("university_configs.domain"), nullable=False, index=True
    )
    name = db.Column(db.String(100), nullable=False)  # e.g. "Autumn Term 2026"
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=False, nullable=False)
    is_complete = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    seasonal_snapshots = db.relationship("SeasonalSnapshot", backref="season", lazy=True)

    def __repr__(self):
        return f"<Season id={self.id} name={self.name}>"


# ──────────────────────────────────────────────
# Weekly Leaderboard Snapshot
# ──────────────────────────────────────────────
class WeeklySnapshot(db.Model):
    __tablename__ = "weekly_snapshots"
    __table_args__ = (
        db.UniqueConstraint("university_domain", "week_start", "rank", name="uq_weekly_snapshot_rank"),
        db.Index("ix_weekly_snapshot_domain_week", "university_domain", "week_start"),
    )

    id = db.Column(db.Integer, primary_key=True)
    university_domain = db.Column(
        db.String(100), db.ForeignKey("university_configs.domain"), nullable=False
    )
    week_start = db.Column(db.DateTime, nullable=False)  # Monday 00:00 UTC
    week_end = db.Column(db.DateTime, nullable=False)    # Sunday 23:59:59 UTC
    rank = db.Column(db.Integer, nullable=False)         # 1–10

    # Frozen at archive time — never recalculated
    display_name = db.Column(db.String(80), nullable=False)
    kg_saved = db.Column(db.Numeric(10, 2, asdecimal=False), nullable=False)
    transaction_count = db.Column(db.Integer, nullable=False)

    # Nullable FK for GDPR deletion (nulled if user deletes account post-snapshot)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    archived_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", backref=db.backref("weekly_snapshots", lazy=True))

    def __repr__(self):
        return f"<WeeklySnapshot domain={self.university_domain} week={self.week_start} rank={self.rank}>"


# ──────────────────────────────────────────────
# Seasonal Leaderboard Snapshot (Hall of Fame)
# ──────────────────────────────────────────────
class SeasonalSnapshot(db.Model):
    __tablename__ = "seasonal_snapshots"
    __table_args__ = (
        db.UniqueConstraint("season_id", "rank", name="uq_seasonal_snapshot_rank"),
        db.Index("ix_seasonal_snapshot_domain", "university_domain"),
    )

    id = db.Column(db.Integer, primary_key=True)
    season_id = db.Column(db.Integer, db.ForeignKey("seasons.id"), nullable=False)
    university_domain = db.Column(
        db.String(100), db.ForeignKey("university_configs.domain"), nullable=False
    )
    rank = db.Column(db.Integer, nullable=False)         # 1–10

    # Frozen at archive time — never recalculated
    display_name = db.Column(db.String(80), nullable=False)
    kg_saved = db.Column(db.Numeric(10, 2, asdecimal=False), nullable=False)
    transaction_count = db.Column(db.Integer, nullable=False)

    # Nullable FK for GDPR deletion
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    archived_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", backref=db.backref("seasonal_snapshots", lazy=True))

    def __repr__(self):
        return f"<SeasonalSnapshot season_id={self.season_id} rank={self.rank}>"

