"""
Reuni — Application Configuration
"""

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration shared across all environments."""
    SECRET_KEY = os.environ.get("SECRET_KEY")
    BASE_URL = os.environ.get("BASE_URL", "http://localhost:5000")
    # Database Configuration
    _db_url = os.environ.get("DATABASE_URL")
    if _db_url and _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = _db_url or (
        "sqlite:///" + os.path.join(basedir, "..", "instance", "reuni.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Background Scheduler Config
    SCHEDULER_ENABLED = os.environ.get("SCHEDULER_ENABLED", "true").lower() == "true"

    LATE_THRESHOLD_HOURS = 24
    AUTO_EXPIRY_HOURS = 72

    # Session cookie security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 7 * 24 * 60 * 60  # 7 days in seconds

    # Limit file uploads to 5MB
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # Password policy
    MIN_PASSWORD_LENGTH = 8

    # Set of university domains permitted to register.
    # Use a Python set literal — {'brookes.ac.uk'} is a set, not a dict.
    # To open to ALL .ac.uk universities, set this to an empty set: set()
    # Never use a plain string comparison — always use set membership.
    _raw_domains = os.environ.get("ALLOWED_UNIVERSITY_DOMAINS", "brookes.ac.uk")
    ALLOWED_UNIVERSITY_DOMAINS: set = set(
        d.strip().lower() for d in _raw_domains.split(",") if d.strip()
    )

    # Brevo Configuration
    BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
    BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL")
    MAIL_DEFAULT_SENDER = os.environ.get("BREVO_SENDER_EMAIL", "support@reuni.ac.uk")

    # Cloudflare R2 Configuration
    STORAGE_PROVIDER = os.environ.get("STORAGE_PROVIDER", "local")
    CF_R2_ACCESS_KEY_ID = os.environ.get("CF_R2_ACCESS_KEY_ID")
    CF_R2_SECRET_ACCESS_KEY = os.environ.get("CF_R2_SECRET_ACCESS_KEY")
    CF_R2_ENDPOINT_URL = os.environ.get("CF_R2_ENDPOINT_URL")
    CF_R2_BUCKET_NAME = os.environ.get("CF_R2_BUCKET_NAME")
    CF_R2_PUBLIC_URL = os.environ.get("CF_R2_PUBLIC_URL")


class DevelopmentConfig(Config):
    """Development-specific settings."""
    DEBUG = True
    # Allow a fallback secret key ONLY in development
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    SESSION_COOKIE_SECURE = False


class TestingConfig(Config):
    """Testing-specific settings."""
    TESTING = True
    SECRET_KEY = "testing-secret-key-not-for-production"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False
    STORAGE_PROVIDER = "local"

    
    # For testing, we also allow university.ac.uk so existing tests pass
    ALLOWED_UNIVERSITY_DOMAINS = {"brookes.ac.uk", "university.ac.uk"}
    
    # Suppress real emails during tests
    MAIL_SUPPRESS_SEND = True
    PROPAGATE_EXCEPTIONS = False


class ProductionConfig(Config):
    """Production-specific settings."""
    DEBUG = False
    SESSION_COOKIE_SECURE = True

    @classmethod
    def init_app(cls, app):
        """Validate critical config on production startup."""
        if not cls.SECRET_KEY:
            raise RuntimeError(
                "SECRET_KEY environment variable is not set. "
                "Refusing to start in production without a secure secret key."
            )
        if not cls.BASE_URL:
            raise RuntimeError(
                "BASE_URL environment variable is not set. "
                "All email links (PIN notifications, cancellation emails, password resets) "
                "will be broken without it. Set BASE_URL=https://your-domain.com in your "
                "Railway environment variables."
            )
        if cls.STORAGE_PROVIDER == "r2":
            missing_r2_vars = [
                var for var in ["CF_R2_ACCESS_KEY_ID", "CF_R2_SECRET_ACCESS_KEY", 
                                "CF_R2_ENDPOINT_URL", "CF_R2_BUCKET_NAME", "CF_R2_PUBLIC_URL"]
                if not getattr(cls, var)
            ]
            if missing_r2_vars:
                raise RuntimeError(
                    f"R2 storage is enabled but the following environment variables are missing: "
                    f"{', '.join(missing_r2_vars)}."
                )
