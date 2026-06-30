import pytest
from unittest.mock import patch, MagicMock
from flask import url_for
from app.utils.turnstile import verify_turnstile

def test_csp_headers_contain_cloudflare_domains(client):
    """Verify that the updated CSP headers permit Cloudflare Turnstile and Analytics domains."""
    response = client.get("/")
    csp = response.headers.get("Content-Security-Policy")
    assert csp is not None
    
    # Check script-src
    assert "script-src 'self' https://challenges.cloudflare.com https://static.cloudflareinsights.com" in csp
    
    # Check connect-src
    assert "connect-src 'self' https://challenges.cloudflare.com https://static.cloudflareinsights.com" in csp
    
    # Check frame-src
    assert "frame-src 'self' https://challenges.cloudflare.com" in csp


def test_verify_turnstile_bypassed_in_testing(app):
    """Verify that verify_turnstile automatically returns True in testing mode."""
    with app.app_context():
        assert verify_turnstile("dummy-token") is True


def test_verify_turnstile_with_dummy_secret(app):
    """Verify that verify_turnstile returns True when the dummy developer secret is used."""
    with app.app_context():
        # Temporarily mock config values as if we are NOT in testing mode
        app.config["TESTING"] = False
        app.config["TURNSTILE_SECRET_KEY"] = "1x00000000000000000000000000000000FF"
        
        try:
            assert verify_turnstile("dummy-token") is True
        finally:
            # Restore testing config
            app.config["TESTING"] = True


@patch("requests.post")
def test_verify_turnstile_api_success(mock_post, app):
    """Verify verify_turnstile returns True when the Cloudflare siteverify API returns success."""
    with app.app_context():
        app.config["TESTING"] = False
        app.config["TURNSTILE_SECRET_KEY"] = "real-secret-key"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response
        
        try:
            assert verify_turnstile("valid-token") is True
            mock_post.assert_called_once_with(
                "https://challenges.cloudflare.com/turnstile/v0/siteverify",
                data={"secret": "real-secret-key", "response": "valid-token"},
                timeout=5
            )
        finally:
            app.config["TESTING"] = True


@patch("requests.post")
def test_verify_turnstile_api_failure(mock_post, app):
    """Verify verify_turnstile returns False when Cloudflare siteverify API returns failure."""
    with app.app_context():
        app.config["TESTING"] = False
        app.config["TURNSTILE_SECRET_KEY"] = "real-secret-key"
        
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": False, "error-codes": ["invalid-input-response"]}
        mock_post.return_value = mock_response
        
        try:
            assert verify_turnstile("invalid-token") is False
        finally:
            app.config["TESTING"] = True


@patch("app.routes.auth.verify_turnstile")
def test_register_route_blocks_on_turnstile_failure(mock_verify, client):
    """Verify that user registration POST is blocked when Turnstile verification fails."""
    mock_verify.return_value = False
    
    response = client.post("/auth/register", data={
        "email": "test@brookes.ac.uk",
        "name": "Test User",
        "password": "SecurePassword123",
        "confirm_password": "SecurePassword123",
        "cf-turnstile-response": "failed-token"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Security verification failed" in response.data


@patch("app.routes.auth.verify_turnstile")
def test_login_route_blocks_on_turnstile_failure(mock_verify, client):
    """Verify that login POST is blocked when Turnstile verification fails."""
    mock_verify.return_value = False
    
    response = client.post("/auth/login", data={
        "email": "test@brookes.ac.uk",
        "password": "SecurePassword123",
        "cf-turnstile-response": "failed-token"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Security verification failed" in response.data


@patch("app.routes.auth.verify_turnstile")
def test_forgot_password_route_blocks_on_turnstile_failure(mock_verify, client):
    """Verify that forgot password POST is blocked when Turnstile verification fails."""
    mock_verify.return_value = False
    
    response = client.post("/auth/forgot-password", data={
        "email": "test@brookes.ac.uk",
        "cf-turnstile-response": "failed-token"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Security verification failed" in response.data
