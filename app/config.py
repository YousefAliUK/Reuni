"""
UniCycle — Application Configuration
"""

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Base configuration shared across all environments."""
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///" + os.path.join(basedir, "..", "instance", "unicycle.db"),
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session cookie security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Password policy
    MIN_PASSWORD_LENGTH = 8


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
