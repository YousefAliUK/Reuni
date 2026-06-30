import os
import requests
from flask import current_app

def verify_turnstile(token: str, remote_ip: str = None) -> bool:
    """
    Verifies Cloudflare Turnstile token with Cloudflare's siteverify API.
    Returns True if valid, or if Turnstile is bypassed in development/testing.
    """
    # Bypass for unit tests or active penetration testing simulation
    if current_app.config.get("TESTING") or os.environ.get("DISABLE_RATE_LIMITS_FOR_PENTEST") == "True":
        return True

    site_key = current_app.config.get("TURNSTILE_SITE_KEY")
    secret_key = current_app.config.get("TURNSTILE_SECRET_KEY")

    # If secret key is not set
    if not secret_key:
        if current_app.config.get("DEBUG"):
            current_app.logger.warning(
                "Turnstile SECRET_KEY not configured. Bypassing validation in development mode."
            )
            return True
        else:
            current_app.logger.error(
                "SECURITY: Turnstile SECRET_KEY is missing in production! Blocking request."
            )
            return False

    # Bypass for Cloudflare dummy testing secret key
    if secret_key == "1x00000000000000000000000000000000FF":
        return True

    if not token:
        current_app.logger.warning("SECURITY: Turnstile validation failed: missing token.")
        return False

    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    data = {
        "secret": secret_key,
        "response": token
    }
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        response = requests.post(url, data=data, timeout=5)
        res_data = response.json()
        if res_data.get("success"):
            return True
        else:
            current_app.logger.warning(
                f"SECURITY: Turnstile verification failed. Errors: {res_data.get('error-codes')}"
            )
            return False
    except Exception as e:
        current_app.logger.error(f"Error connecting to Cloudflare Turnstile API: {e}")
        # In case of API failure, fail-closed in production but fail-open in debug mode
        return current_app.config.get("DEBUG", False)
