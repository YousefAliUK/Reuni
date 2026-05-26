"""
UniCycle — Configuration Tests
Verifies that each config class has the correct settings.
"""

from app import create_app
from app.config import DevelopmentConfig, TestingConfig, ProductionConfig


class TestAppConfig:

    def test_testing_config(self, app):
        """TestingConfig should enable TESTING and use in-memory SQLite."""
        assert app.config["TESTING"] is True
        assert ":memory:" in app.config["SQLALCHEMY_DATABASE_URI"]

    def test_development_config(self):
        """DevelopmentConfig should enable DEBUG."""
        dev_app = create_app(DevelopmentConfig)
        assert dev_app.config["DEBUG"] is True
        assert dev_app.config["TESTING"] is not True

    def test_production_config(self):
        """ProductionConfig should refuse to start without SECRET_KEY."""
        import pytest
        # Production should raise RuntimeError if SECRET_KEY is not set
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            create_app(ProductionConfig)

    def test_production_config_debug_disabled(self):
        """ProductionConfig should have DEBUG disabled."""
        assert ProductionConfig.DEBUG is False

    def test_app_factory_returns_flask_app(self, app):
        """create_app() should return a Flask application instance."""
        from flask import Flask
        assert isinstance(app, Flask)

    def test_secret_key_is_set(self, app):
        """App must have a SECRET_KEY configured."""
        assert app.config["SECRET_KEY"] is not None
        assert len(app.config["SECRET_KEY"]) > 0
