"""
UniCycle — Auth Routes (Blueprint)
Handles user registration, login, and logout.
"""

import re

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def _normalise_phone(raw: str) -> str:
    """
    Strips spaces, dashes, and parentheses from the input.
    If it starts with '0' (UK format like 07912345678), replace leading 0 with '+44'.
    If it starts with '+', keep it as-is (international number).
    If it starts with '44' (without +), prepend '+'.
    """
    cleaned = raw.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if cleaned.startswith("0"):
        return "+44" + cleaned[1:]
    elif cleaned.startswith("+"):
        return cleaned
    elif cleaned.startswith("44"):
        return "+" + cleaned
    else:
        # Fallback/assume it's UK or local without lead zero if short, but E.164-ish
        return cleaned


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        name = request.form.get("name", "").strip()
        phone_raw = request.form.get("phone_number", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # --- Basic validation ---
        if not email or not name or not password or not phone_raw:
            flash("All fields are required.", "danger")
            return redirect(url_for("auth.register"))

        # Email format validation
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash("Please enter a valid email address.", "danger")
            return redirect(url_for("auth.register"))

        # Password strength validation
        min_pw_len = current_app.config.get("MIN_PASSWORD_LENGTH", 8)
        if len(password) < min_pw_len:
            flash(f"Password must be at least {min_pw_len} characters long.", "danger")
            return redirect(url_for("auth.register"))

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register"))

        # Check for existing email OR phone — use generic message to prevent enumeration
        existing_email = User.query.filter_by(email=email).first()
        phone_number = _normalise_phone(phone_raw)

        if not re.match(r'^\+\d{10,15}$', phone_number):
            flash("Please enter a valid phone number.", "danger")
            return redirect(url_for("auth.register"))

        existing_phone = User.query.filter_by(phone_number=phone_number).first()

        if existing_email or existing_phone:
            flash("An account with these details already exists.", "danger")
            return redirect(url_for("auth.register"))

        # --- Create user ---
        user = User(email=email, name=name, phone_number=phone_number)
        user.set_password(password)
        db.session.add(user)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during registration: {e}")
            flash("A registration error occurred. Please try again.", "danger")
            return redirect(url_for("auth.register"))

        login_user(user)
        flash("Welcome to UniCycle! 🎉", "success")
        return redirect(url_for("index"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        login_user(user)
        flash(f"Welcome back, {user.name}!", "success")

        # Redirect to the page the user originally wanted, or home.
        # Security: only allow relative redirects (prevent open-redirect attacks).
        next_page = request.args.get("next")
        if next_page:
            from urllib.parse import urlparse
            parsed = urlparse(next_page)
            # Reject absolute URLs, protocol-relative URLs, and any with scheme/netloc
            if parsed.netloc or parsed.scheme or next_page.startswith("//"):
                next_page = None  # reject unsafe URLs
        return redirect(next_page or url_for("index"))

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))
