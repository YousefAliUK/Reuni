import re
import secrets
import hashlib
from datetime import datetime, timezone, timedelta
from html import escape as html_escape

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.emails import send_email

from app import db, limiter
from app.models import User
from app.utils.email_validation import extract_university_domain, is_domain_allowed
from app.utils.tokens import generate_password_reset_token, verify_password_reset_token
from app.utils.turnstile import verify_turnstile
from itsdangerous import URLSafeTimedSerializer
from flask_limiter.util import get_remote_address

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def send_otp_email(name: str, email: str, code: str):
    safe_name = html_escape(name)
    safe_code = html_escape(code)
    email_html = (
        f"<p>Hi {safe_name},</p>\n"
        f"<p>Your 6-digit verification code to activate your Reuni account is:</p>\n"
        f"<div class=\"code-block\">{safe_code}</div>\n"
        f"<p>This code is valid for 15 minutes. Please complete your registration on the website.</p>\n"
        f"<p>If you didn't create an account, you can safely ignore this email.</p>\n"
        f"<p>Best regards,<br>The Reuni Team</p>"
    )
    send_email(email, name, "Activate your Reuni Account", email_html)


def resend_key_func():
    if request.method == "POST":
        return request.form.get("email", "").strip().lower()
    return get_remote_address()


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("5 per hour", key_func=get_remote_address)
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        # --- Turnstile validation ---
        turnstile_token = request.form.get("cf-turnstile-response", "")
        if not verify_turnstile(turnstile_token, remote_ip=request.remote_addr):
            flash("Security verification failed. Please try again.", "danger")
            return redirect(url_for("auth.register"))

        email = request.form.get("email", "").strip().lower()
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # --- Basic validation ---
        if not email or not name or not password:
            flash("All fields are required.", "danger")
            return redirect(url_for("auth.register"))

        if len(name) > 80:
            flash("Name must be 80 characters or fewer.", "danger")
            return redirect(url_for("auth.register"))

        # Validate university domain
        domain = extract_university_domain(email)
        if not domain:
            flash("Please register with a valid institutional email address (e.g., @brookes.ac.uk).", "danger")
            return redirect(url_for("auth.register"))
            
        if not is_domain_allowed(domain, current_app.config.get("ALLOWED_UNIVERSITY_DOMAINS", set())):
            flash("Reuni is not yet available at your university.", "danger")
            return redirect(url_for("auth.register"))

        # Password strength validation
        min_pw_len = current_app.config.get("MIN_PASSWORD_LENGTH", 8)
        max_pw_len = current_app.config.get("MAX_PASSWORD_LENGTH", 128)
        if len(password) < min_pw_len:
            flash(f"Password must be at least {min_pw_len} characters long.", "danger")
            return redirect(url_for("auth.register"))

        if len(password) > max_pw_len:
            flash(f"Password must be {max_pw_len} characters or fewer.", "danger")
            return redirect(url_for("auth.register"))

        if (not any(c.isupper() for c in password) or
            not any(c.islower() for c in password) or
            not any(c.isdigit() for c in password)):
            flash("Password must contain at least one uppercase letter, one lowercase letter, and one digit.", "danger")
            return redirect(url_for("auth.register"))

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register"))

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Check for existing email
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            if existing_email.deletion_pending_until:
                # Account is pending deletion (cooldown period)
                if existing_email.deletion_pending_until <= now:
                    # Cooldown has expired, anonymise immediately to free the email
                    try:
                        existing_email.anonymise()
                        db.session.commit()
                    except Exception as clean_err:
                        db.session.rollback()
                        current_app.logger.error(f"Error during JIT registration cleanup of expired account {existing_email.id}: {clean_err}")
                        flash("A registration error occurred. Please try again.", "danger")
                        return redirect(url_for("auth.register"))
                else:
                    # Still in cooldown — silently redirect as if registration succeeded (blocks enumeration)
                    session["verify_email"] = email
                    flash("A verification code has been sent to your email.", "info")
                    return redirect(url_for("auth.verify_email"))
            elif existing_email.is_verified:
                # Already exists — silently redirect (no email sent, no info leaked)
                session["verify_email"] = email
                flash("A verification code has been sent to your email.", "info")
                return redirect(url_for("auth.verify_email"))
            else:
                db.session.delete(existing_email)
                db.session.commit()

        # --- Create user ---
        user = User(
            email=email,
            name=name,
            university_domain=domain,
            is_verified=False
        )
        user.set_password(password)

        # Generate verification code
        otp_code = f"{secrets.randbelow(1000000):06d}"
        user.email_verification_code = generate_password_hash(otp_code)
        user.email_verification_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15)
        user.email_verification_attempts = 0

        from sqlalchemy.exc import IntegrityError
        db.session.add(user)
        try:
            db.session.commit()
            email_hash = hashlib.sha256(email.encode('utf-8')).hexdigest()[:16]
            current_app.logger.info(f"SECURITY: User registration successful for email_hash={email_hash} (user={user.id})")
        except IntegrityError as e:
            db.session.rollback()
            # Silently redirect as if registration succeeded to block enumeration
            session["verify_email"] = email
            flash("A verification code has been sent to your email.", "info")
            return redirect(url_for("auth.verify_email"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during registration: {e}")
            flash("A registration error occurred. Please try again.", "danger")
            return redirect(url_for("auth.register"))

        # Send email outside database transaction
        try:
            send_otp_email(user.name, email, otp_code)
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email to user {user.id}: {e}")

        session['verify_email'] = email
        flash("A verification code has been sent to your email.", "info")
        return redirect(url_for("auth.verify_email"))

    return render_template("auth/register.html")


def login_limit_key():
    email = request.form.get("email", "").strip().lower()
    return f"{get_remote_address()}:{email}"


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", key_func=login_limit_key)
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        # --- Turnstile validation ---
        turnstile_token = request.form.get("cf-turnstile-response", "")
        if not verify_turnstile(turnstile_token, remote_ip=request.remote_addr):
            flash("Security verification failed. Please try again.", "danger")
            return redirect(url_for("auth.login"))

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if email.endswith("@deleted.reuni") or email.startswith("deleted_"):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(email=email).first()
        email_hash = hashlib.sha256(email.encode('utf-8')).hexdigest()[:16]

        if user:
            # Block login if the account is deactivated or pending deletion
            if user.deletion_pending_until is not None:
                flash("Invalid email or password.", "danger")
                return redirect(url_for("auth.login"))
            # 1. Check lockout status first
            if user.locked_until and user.locked_until > datetime.now(timezone.utc).replace(tzinfo=None):
                flash("Invalid email or password.", "danger")
                return redirect(url_for("auth.login"))

            # 2. Verify password
            if not user.check_password(password):
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15)
                    user.failed_login_attempts = 0
                    db.session.commit()
                    current_app.logger.warning(f"SECURITY: Account {user.id} locked after 5 failed attempts from {request.remote_addr}")
                    flash("Invalid email or password.", "danger")
                else:
                    db.session.commit()
                    current_app.logger.warning(f"SECURITY: Failed login attempt for email_hash={email_hash} from {request.remote_addr} (attempt {user.failed_login_attempts}/5)")
                    flash("Invalid email or password.", "danger")
                return redirect(url_for("auth.login"))

            # 3. Successful verification - reset attempts & lockout
            user.failed_login_attempts = 0
            user.locked_until = None
            db.session.commit()
        else:
            current_app.logger.warning(f"SECURITY: Failed login attempt for unknown email_hash={email_hash} from {request.remote_addr}")
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        if not user.is_verified:
            # Save email in session to allow verification
            session['verify_email'] = email
            flash("Please verify your email before logging in. Check your inbox or resend the verification code.", "warning")
            return redirect(url_for("auth.resend_verification"))

        if not user.is_active:
            flash("This account has been deactivated. Contact support.", "danger")
            return redirect(url_for("auth.login"))

        # Regenerate session to prevent session fixation attacks
        session.clear()
        login_user(user)
        current_app.logger.info(f"SECURITY: Successful login for user {user.id} from {request.remote_addr}")

        if user.role == 'partner':
            session['logged_in_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        flash(f"Welcome back, {user.name}.", "success")

        correct_subdomain = None
        if user.university_domain:
            from app import get_subdomain_map
            uni_map = get_subdomain_map()
            rev_map = {v: k for k, v in uni_map.items()}
            correct_subdomain = rev_map.get(user.university_domain)

        next_page = request.args.get("next")
        if next_page:
            from urllib.parse import urlparse
            parsed = urlparse(next_page)
            if parsed.netloc or parsed.scheme or next_page.startswith("//"):
                next_page = None
                
        if next_page:
            return redirect(next_page)
        elif correct_subdomain:
            # Redirect directly to their university subdomain marketplace
            from urllib.parse import urlsplit, urlparse
            base_url = current_app.config.get("BASE_URL") or "http://localhost:5000"
            base_parsed = urlsplit(base_url)
            trusted_host = base_parsed.hostname.lower() if base_parsed.hostname else "localhost"
            
            req_parsed = urlsplit(request.host_url)
            req_host = req_parsed.hostname.lower() if req_parsed.hostname else ""
            
            # Verify if request host matches or is a subdomain of the trusted base domain
            if (req_host == "localhost" or req_host.endswith(".localhost")) and (trusted_host == "localhost" or trusted_host.endswith(".localhost")):
                base_domain = "localhost"
            elif req_host == trusted_host or req_host.endswith("." + trusted_host):
                parts = trusted_host.split('.')
                if len(parts) >= 3 and parts[-2:] == ['ac', 'uk']:
                    base_domain = '.'.join(parts[-3:])
                elif len(parts) >= 3 and parts[-2:] == ['co', 'uk']:
                    base_domain = '.'.join(parts[-3:])
                else:
                    base_domain = '.'.join(parts[-2:]) if len(parts) >= 2 else trusted_host
            else:
                parts = trusted_host.split('.')
                if len(parts) >= 3 and parts[-2:] == ['ac', 'uk']:
                    base_domain = '.'.join(parts[-3:])
                elif len(parts) >= 3 and parts[-2:] == ['co', 'uk']:
                    base_domain = '.'.join(parts[-3:])
                else:
                    base_domain = '.'.join(parts[-2:]) if len(parts) >= 2 else trusted_host

            port = req_parsed.port or base_parsed.port
            new_host = f"{correct_subdomain}.{base_domain}"
            if port:
                new_host = f"{new_host}:{port}"
            return redirect(f"{request.scheme}://{new_host}/")
        else:
            return redirect(url_for("index"))

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@auth_bp.route("/verify-email", methods=["GET", "POST"])
def verify_email():
    if current_user.is_authenticated and current_user.is_verified:
        return redirect(url_for("index"))

    verify_email_address = session.get("verify_email")
    if not verify_email_address:
        flash("Your session expired. Enter your email to get a new code.", "warning")
        return redirect(url_for("auth.resend_verification"))

    if request.method == "POST":
        user = User.query.filter_by(email=verify_email_address).first()

        if not user:
            flash("No account found. Please register again.", "danger")
            session.pop("verify_email", None)
            return redirect(url_for("auth.register"))

        if user.is_verified:
            flash("Your account is already verified.", "info")
            session.pop("verify_email", None)
            return redirect(url_for("auth.login"))

        now = datetime.now(timezone.utc).replace(tzinfo=None)

        if not user.email_verification_code or not user.email_verification_expires_at or user.email_verification_expires_at < now:
            flash("This verification code has expired. Please request a new one.", "danger")
            return redirect(url_for("auth.resend_verification"))

        if user.email_verification_attempts >= 5:
            user.email_verification_code = None
            user.email_verification_expires_at = None
            user.email_verification_attempts = 0
            db.session.commit()
            flash("Too many incorrect attempts. Please request a new verification code.", "danger")
            return redirect(url_for("auth.resend_verification"))

        entered_code = request.form.get("code", "").strip()

        if check_password_hash(user.email_verification_code, entered_code):
            user.is_verified = True
            user.email_verification_code = None
            user.email_verification_expires_at = None
            user.email_verification_attempts = 0
            db.session.commit()

            flash("Email verified. You can now log in.", "success")
            session.pop("verify_email", None)
            return redirect(url_for("auth.login"))
        else:
            user.email_verification_attempts += 1
            db.session.commit()

            if user.email_verification_attempts >= 5:
                user.email_verification_code = None
                user.email_verification_expires_at = None
                user.email_verification_attempts = 0
                db.session.commit()
                flash("Too many incorrect attempts. Please request a new verification code.", "danger")
                return redirect(url_for("auth.resend_verification"))

            remaining = 5 - user.email_verification_attempts
            flash(f"Incorrect verification code. You have {remaining} attempts remaining.", "danger")
            return redirect(url_for("auth.verify_email"))

    return render_template("auth/verify_email.html", email=verify_email_address)


@auth_bp.route("/resend-verification", methods=["GET", "POST"])
@limiter.limit("10 per hour", key_func=resend_key_func)
def resend_verification():
    if current_user.is_authenticated and current_user.is_verified:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        user = User.query.filter_by(email=email).first()

        if user and not user.is_verified:
            otp_code = f"{secrets.randbelow(1000000):06d}"
            user.email_verification_code = generate_password_hash(otp_code)
            user.email_verification_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15)
            user.email_verification_attempts = 0
            db.session.commit()

            try:
                send_otp_email(user.name, email, otp_code)
            except Exception as e:
                current_app.logger.error(f"Failed to send resend email to user {user.id}: {e}")

        session['verify_email'] = email
        flash("If that email is registered and unverified, we've sent a new verification code.", "success")
        return redirect(url_for("auth.verify_email"))

    return render_template("auth/resend_verification.html")


@auth_bp.route("/invite/<token>", methods=["GET", "POST"])
def invite_register(token):
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    from app.utils.tokens import verify_partner_invite_token
    university_domain = verify_partner_invite_token(token, current_app.config["SECRET_KEY"])
    if not university_domain:
        flash("This invite link is invalid or has expired.", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            flash("All fields are required.", "danger")
            return render_template("partner/invite_register.html", token=token, university_domain=university_domain)

        if len(name) > 80:
            flash("Name must be 80 characters or fewer.", "danger")
            return render_template("partner/invite_register.html", token=token, university_domain=university_domain)

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("partner/invite_register.html", token=token, university_domain=university_domain)

        # Validate password constraints
        min_pw_len = current_app.config.get("MIN_PASSWORD_LENGTH", 8)
        max_pw_len = current_app.config.get("MAX_PASSWORD_LENGTH", 128)
        if len(password) < min_pw_len:
            flash(f"Password must be at least {min_pw_len} characters long.", "danger")
            return render_template("partner/invite_register.html", token=token, university_domain=university_domain)

        if len(password) > max_pw_len:
            flash(f"Password must be {max_pw_len} characters or fewer.", "danger")
            return render_template("partner/invite_register.html", token=token, university_domain=university_domain)

        if (not any(c.isupper() for c in password) or
            not any(c.islower() for c in password) or
            not any(c.isdigit() for c in password)):
            flash("Password must contain at least one uppercase letter, one lowercase letter, and one digit.", "danger")
            return render_template("partner/invite_register.html", token=token, university_domain=university_domain)

        # Validate domain
        email_domain = extract_university_domain(email)
        if not email_domain or (email_domain != university_domain and not email_domain.endswith("." + university_domain)):
            flash(f"Please use your institutional email address for {university_domain}.", "danger")
            return render_template("partner/invite_register.html", token=token, university_domain=university_domain)

        # Check if email is already in use
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("An account with this email already exists.", "danger")
            return render_template("partner/invite_register.html", token=token, university_domain=university_domain)

        # Create partner user
        user = User(
            email=email,
            name=name,
            role="partner",
            partner_university=university_domain,
            university_domain=email_domain,
            is_verified=True,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during partner registration: {e}")
            flash("A registration error occurred. Please try again.", "danger")
            return render_template("partner/invite_register.html", token=token, university_domain=university_domain)

        # Send welcome email
        try:
            base = current_app.config.get("BASE_URL", "").rstrip("/")
            login_url = f"{base}{url_for('auth.login')}"
            safe_name = html_escape(name)
            safe_domain = html_escape(university_domain)
            email_html = (
                f"<p>Hello {safe_name},</p>\n"
                f"<p>Your Reuni partner account for <strong>{safe_domain}</strong> has been successfully created.</p>\n"
                f"<p>Click the button below to log in and access your partner dashboard.</p>\n"
                f"<div style=\"text-align:center; margin: 24px 0;\">\n"
                f"    <a href=\"{login_url}\" class=\"btn-primary\">Log In to Dashboard</a>\n"
                f"</div>\n"
                f"<p>— The Reuni team</p>"
            )
            send_email(
                to_email=email,
                to_name=name,
                subject="Welcome to Reuni Partner Dashboard",
                html_content=email_html
            )
        except Exception as e:
            current_app.logger.error(f"Failed to send partner welcome email: {e}")

        flash("Partner account created. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("partner/invite_register.html", token=token, university_domain=university_domain)


def forgot_password_key_func():
    if request.method == "POST":
        return request.form.get('email', '').strip().lower()
    return get_remote_address()


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("3 per hour", key_func=forgot_password_key_func)
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        # --- Turnstile validation ---
        turnstile_token = request.form.get("cf-turnstile-response", "")
        if not verify_turnstile(turnstile_token, remote_ip=request.remote_addr):
            flash("Security verification failed. Please try again.", "danger")
            return redirect(url_for("auth.forgot_password"))

        email = request.form.get("email", "").strip().lower()
        if email:
            if email.endswith("@deleted.reuni") or email.startswith("deleted_"):
                flash("If an account exists with that email, a reset link has been sent.", "info")
                return redirect(url_for("auth.forgot_password", success=1))

            user = User.query.filter_by(email=email).first()
            if user and user.is_verified and user.deletion_pending_until is None:
                token = generate_password_reset_token(user.email, user.password_hash, current_app.config["SECRET_KEY"])
                base = current_app.config.get("BASE_URL", "").rstrip("/")
                reset_url = f"{base}{url_for('auth.reset_password', token=token)}"
                
                safe_name = html_escape(user.name)
                email_html = f"""<p>Hi {safe_name},</p>
<p>We received a request to reset the password for your Reuni account.</p>
<p>Click the button below to set a new password. This link expires in 1 hour.</p>
<div style="text-align:center; margin: 24px 0;">
    <a href="{reset_url}" class="btn-primary">Reset Password</a>
</div>
<p>Or copy and paste this URL into your browser:</p>
<p style="word-break: break-all;"><a href="{reset_url}">{reset_url}</a></p>
<p>If you didn't request a password reset, you can safely ignore this email. Your password will not change unless you click the link above.</p>
<p>— The Reuni team</p>"""
                try:
                    send_email(
                        to_email=email,
                        to_name=user.name,
                        subject="Password reset for your Reuni account",
                        html_content=email_html
                    )
                except Exception as e:
                    current_app.logger.warning(f"Failed to send password reset email to user {user.id}: {e}")

        flash("If an account exists with that email, a reset link has been sent.", "info")
        return redirect(url_for("auth.forgot_password", success=1))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    s = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        _, email = s.loads_unsafe(token)
    except Exception:
        email = None

    if not email:
        flash("This reset link is invalid.", "danger")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("This reset link is invalid.", "danger")
        return redirect(url_for("auth.forgot_password"))

    verified_email = verify_password_reset_token(
        token, user.password_hash, current_app.config["SECRET_KEY"]
    )
    if not verified_email:
        flash("This reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not new_password or not confirm_password:
            flash("All password fields are required.", "danger")
            return render_template("auth/reset_password.html", token=token)

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("auth/reset_password.html", token=token)

        if user.check_password(new_password):
            flash("New password must be different from your current password.", "danger")
            return render_template("auth/reset_password.html", token=token)

        min_pw_len = current_app.config.get("MIN_PASSWORD_LENGTH", 8)
        max_pw_len = current_app.config.get("MAX_PASSWORD_LENGTH", 128)
        if len(new_password) < min_pw_len:
            flash(f"Password must be at least {min_pw_len} characters long.", "danger")
            return render_template("auth/reset_password.html", token=token)

        if len(new_password) > max_pw_len:
            flash(f"Password must be {max_pw_len} characters or fewer.", "danger")
            return render_template("auth/reset_password.html", token=token)

        if (not any(c.isupper() for c in new_password) or
            not any(c.islower() for c in new_password) or
            not any(c.isdigit() for c in new_password)):
            flash("Password must contain at least one uppercase letter, one lowercase letter, and one digit.", "danger")
            return render_template("auth/reset_password.html", token=token)

        user.set_password(new_password)
        user.failed_login_attempts = 0
        user.locked_until = None

        try:
            db.session.commit()
            session.pop('reset_token', None)
            current_app.logger.info(f"SECURITY: Password reset completed for user {user.id}")
            flash("Password updated. You can now log in.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during password reset: {e}")
            flash("An error occurred. Please try again.", "danger")
            return render_template("auth/reset_password.html", token=token)

    session['reset_token'] = token
    return render_template("auth/reset_password.html", token=token)




