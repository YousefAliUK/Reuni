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

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 7 * 24 * 60 * 60  # 7 days in seconds

    # Session cookie domain to allow sharing session cookies across subdomains.
    _session_domain = os.environ.get("SESSION_COOKIE_DOMAIN")
    if not _session_domain:
        _url = os.environ.get("BASE_URL") or "http://localhost:5000"
        _base_host = _url.split("://")[-1].split(":")[0].lower()
        if _base_host == "localhost" or _base_host.endswith(".localhost"):
            _session_domain = ".localhost"
        elif _base_host not in ["127.0.0.1", ""]:
            _parts = _base_host.split(".")
            if len(_parts) >= 3 and (
                (_parts[-2] == "ac" and _parts[-1] == "uk") or 
                (_parts[-2] == "co" and _parts[-1] == "uk") or
                (_parts[-2] == "org" and _parts[-1] == "uk") or
                (_parts[-2] == "sch" and _parts[-1] == "uk")
            ):
                _session_domain = f".{'.'.join(_parts[-3:])}"
            elif len(_parts) >= 2:
                _session_domain = f".{'.'.join(_parts[-2:])}"
    SESSION_COOKIE_DOMAIN = _session_domain

    # Limit file uploads to 5MB
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    # Email client timeout
    MAIL_TIMEOUT = os.environ.get("MAIL_TIMEOUT", "30")

    # Password policy
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128

    # Set of university domains permitted to register.
    # Use a Python set literal — {'brookes.ac.uk'} is a set, not a dict.
    # To open to ALL .ac.uk universities, set this to an empty set: set()
    # Never use a plain string comparison — always use set membership.
    _raw_domains = os.environ.get("ALLOWED_UNIVERSITY_DOMAINS", "brookes.ac.uk")
    ALLOWED_UNIVERSITY_DOMAINS: set = set(
        d.strip().lower() for d in _raw_domains.split(",") if d.strip()
    )

    # FALLBACK ONLY — runtime routing reads from UniversityConfig DB table.
    # This is used only if the DB is unavailable (e.g., during initial migration).
    SUBDOMAIN_UNIVERSITY_MAP = {
        "brookes": "brookes.ac.uk",
        "oxford": "oxford.ac.uk",
    }

    FEATURE_MULTI_UNIVERSITY = os.environ.get("FEATURE_MULTI_UNIVERSITY", "false").lower() == "true"

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

    # Cloudflare Turnstile Configuration
    TURNSTILE_SITE_KEY = os.environ.get("TURNSTILE_SITE_KEY")
    TURNSTILE_SECRET_KEY = os.environ.get("TURNSTILE_SECRET_KEY")


class DevelopmentConfig(Config):
    """Development-specific settings."""
    DEBUG = True
    # Allow a fallback secret key ONLY in development
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    SESSION_COOKIE_SECURE = False
    
    _dev_url = os.environ.get("BASE_URL") or "http://localhost:5000"
    SERVER_NAME = _dev_url.split("://")[-1].lower()


class TestingConfig(Config):
    """Testing-specific settings."""
    TESTING = True
    SECRET_KEY = "testing-secret-key-not-for-production"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SESSION_COOKIE_SECURE = False
    RATELIMIT_ENABLED = False
    STORAGE_PROVIDER = "local"
    SESSION_COOKIE_DOMAIN = None

    
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
        if not cls.BASE_URL or cls.BASE_URL == "http://localhost:5000":
            raise RuntimeError(
                "BASE_URL environment variable is not set or defaults to localhost. "
                "All email links (PIN notifications, cancellation emails, password resets) "
                "will be broken without it. Set BASE_URL=https://your-domain.com in your "
                "Railway environment variables."
            )
        if not cls.BREVO_API_KEY:
            raise RuntimeError(
                "BREVO_API_KEY environment variable is not set. "
                "Email functionality (OTP verification, password resets, PIN notifications) "
                "will be completely broken without it."
            )
        db_url = os.environ.get("DATABASE_URL")
        if not db_url or "sqlite" in db_url:
            raise RuntimeError(
                "DATABASE_URL environment variable is not set or points to SQLite. "
                "SQLite is not supported in production to prevent data loss."
            )
        rl_uri = os.environ.get("RATELIMIT_STORAGE_URI")
        if not rl_uri or rl_uri.strip().lower() == "memory://":
            raise RuntimeError(
                "RATELIMIT_STORAGE_URI environment variable is required and cannot be memory:// in production."
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
