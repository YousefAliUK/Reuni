import re
import secrets
from datetime import datetime, timezone, timedelta

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
import brevo_python as brevo
from brevo_python.rest import ApiException

from app import db, mail, limiter
from app.models import User
from app.utils.email_validation import extract_university_domain, is_domain_allowed
from app.utils.tokens import generate_password_reset_token, verify_password_reset_token
from itsdangerous import URLSafeTimedSerializer
from flask_limiter.util import get_remote_address

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


def send_otp_email(name: str, email: str, code: str):
    if current_app.config.get("MAIL_SUPPRESS_SEND"):
        return

    api_key = current_app.config.get("MAIL_PASSWORD")
    if not api_key:
        current_app.logger.warning("Brevo API key (MAIL_PASSWORD) is not set; skipping OTP email send")
        return

    configuration = brevo.Configuration()
    configuration.api_key["api-key"] = api_key
    with brevo.ApiClient(configuration) as api_client:
        api_instance = brevo.TransactionalEmailsApi(api_client)
        sender_email = current_app.config.get("MAIL_DEFAULT_SENDER", "support@reuni.ac.uk")
        from html import escape as html_escape

        safe_name = html_escape(name)
        safe_code = html_escape(code)
        send_smtp_email = brevo.SendSmtpEmail(
            to=[{"email": email, "name": safe_name}],
            sender={"email": sender_email, "name": "Reuni"},
            subject="Your OTP Code",
            html_content=(
                f"<p>Hi {safe_name},</p>"
                f"<p>Your 6-digit verification code to activate your Reuni account is:</p>"
                f"<h2 style='letter-spacing:4px'>{safe_code}</h2>"
                f"<p>This code expires in 15 minutes.</p>"
                f"<p>If you didn't create an account, you can safely ignore this email.</p>"
                f"<p>— The Reuni team</p>"
            ),
        )
        try:
            api_instance.send_transac_email(send_smtp_email)
        except ApiException as e:
            current_app.logger.error(f"Brevo API error sending OTP email to {email}: {e}")


def resend_key_func():
    if request.method == "POST":
        return request.form.get("email", "").strip().lower()
    return get_remote_address()


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

        # Domain format validation
        domain = extract_university_domain(email)
        if domain is None:
            flash("Please use a valid university email address (e.g. yourname@brookes.ac.uk).", "danger")
            return redirect(url_for("auth.register"))

        # Allowed domain enforcement
        if not is_domain_allowed(domain, current_app.config.get("ALLOWED_UNIVERSITY_DOMAINS", set())):
            flash("Reuni is not yet available at your university. We're expanding soon.", "danger")
            return redirect(url_for("auth.register"))

        # Password strength validation
        min_pw_len = current_app.config.get("MIN_PASSWORD_LENGTH", 8)
        if len(password) < min_pw_len:
            flash(f"Password must be at least {min_pw_len} characters long.", "danger")
            return redirect(url_for("auth.register"))

        if (not any(c.isupper() for c in password) or
            not any(c.islower() for c in password) or
            not any(c.isdigit() for c in password)):
            flash("Password must contain at least one uppercase letter, one lowercase letter, and one digit.", "danger")
            return redirect(url_for("auth.register"))

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("auth.register"))

        # Normalise phone number
        phone_number = _normalise_phone(phone_raw)
        if not re.match(r'^\+\d{10,15}$', phone_number):
            flash("Please enter a valid phone number.", "danger")
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
                        flash("An error occurred during registration. Please try again.", "danger")
                        return redirect(url_for("auth.register"))
                else:
                    # Still in cooldown
                    remaining = existing_email.deletion_pending_until - now
                    days = max(1, remaining.days)
                    flash(f"This email is associated with an account pending deletion. You can register a new account in {days} days.", "danger")
                    return redirect(url_for("auth.register"))
            elif existing_email.is_verified:
                flash("An account with this email already exists.", "danger")
                return redirect(url_for("auth.register"))
            else:
                db.session.delete(existing_email)
                db.session.commit()

        # Check for existing phone
        user_with_phone = User.query.filter_by(phone_number=phone_number).first()
        if user_with_phone:
            if user_with_phone.deletion_pending_until:
                # Account is pending deletion
                if user_with_phone.deletion_pending_until <= now:
                    try:
                        user_with_phone.anonymise()
                        db.session.commit()
                    except Exception as clean_err:
                        db.session.rollback()
                        current_app.logger.error(f"Error during JIT registration phone cleanup: {clean_err}")
                        flash("An error occurred during registration. Please try again.", "danger")
                        return redirect(url_for("auth.register"))
                else:
                    remaining = user_with_phone.deletion_pending_until - now
                    days = max(1, remaining.days)
                    flash(f"This phone number is associated with an account pending deletion. You can register a new account in {days} days.", "danger")
                    return redirect(url_for("auth.register"))
            elif user_with_phone.is_verified:
                flash("An account with this phone number already exists.", "danger")
                return redirect(url_for("auth.register"))
            else:
                db.session.delete(user_with_phone)
                db.session.commit()

        # --- Create user ---
        user = User(
            email=email,
            name=name,
            phone_number=phone_number,
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
        except IntegrityError as e:
            db.session.rollback()
            existing_email = User.query.filter_by(email=email).first()
            existing_phone = User.query.filter_by(phone_number=phone_number).first()
            if (existing_email and existing_email.is_verified) or (existing_phone and existing_phone.is_verified):
                flash("An account with this email or phone number already exists.", "danger")
            else:
                flash("An account with this email or phone number is currently pending registration. Please try again shortly.", "danger")
            return redirect(url_for("auth.register"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during registration: {e}")
            flash("A registration error occurred. Please try again.", "danger")
            return redirect(url_for("auth.register"))

        # Send email outside database transaction
        try:
            send_otp_email(user.name, email, otp_code)
        except Exception as e:
            current_app.logger.error(f"Failed to send verification email: {e}")

        session['verify_email'] = email
        flash("We've sent a 6-digit verification code to your university email. Please check your inbox.", "success")
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
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if email.endswith("@deleted.reuni") or email.startswith("deleted_"):
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth.login"))

        user = User.query.filter_by(email=email).first()

        if user:
            # Block login if the account is deactivated or pending deletion
            if user.deletion_pending_until is not None:
                flash("Invalid email or password.", "danger")
                return redirect(url_for("auth.login"))
            # 1. Check lockout status first
            if user.locked_until and user.locked_until > datetime.now(timezone.utc).replace(tzinfo=None):
                remaining = int((user.locked_until - datetime.now(timezone.utc).replace(tzinfo=None)).total_seconds() / 60)
                flash(f"This account has been locked due to too many failed login attempts. Please try again in {max(1, remaining)} minutes.", "danger")
                return redirect(url_for("auth.login"))

            # 2. Verify password
            if not user.check_password(password):
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.locked_until = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=15)
                    user.failed_login_attempts = 0
                    db.session.commit()
                    flash("Too many failed login attempts. This account has been locked for 15 minutes.", "danger")
                else:
                    db.session.commit()
                    flash("Invalid email or password.", "danger")
                return redirect(url_for("auth.login"))

            # 3. Successful verification - reset attempts & lockout
            user.failed_login_attempts = 0
            user.locked_until = None
            db.session.commit()
        else:
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

        login_user(user)
        if user.role == 'partner':
            session['logged_in_at'] = datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
        flash(f"Welcome back, {user.name}.", "success")

        next_page = request.args.get("next")
        if next_page:
            from urllib.parse import urlparse
            parsed = urlparse(next_page)
            if parsed.netloc or parsed.scheme or next_page.startswith("//"):
                next_page = None
        return redirect(next_page or url_for("index"))

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
                current_app.logger.error(f"Failed to send resend email: {e}")

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

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("partner/invite_register.html", token=token, university_domain=university_domain)

        # Validate password length
        min_pw_len = current_app.config.get("MIN_PASSWORD_LENGTH", 8)
        if len(password) < min_pw_len:
            flash(f"Password must be at least {min_pw_len} characters long.", "danger")
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
            msg = Message(
                subject="Welcome to Reuni Partner Dashboard",
                recipients=[email]
            )
            msg.body = f"Hello {name},\n\nYour Reuni partner account for {university_domain} has been successfully created. You can now log in to access the dashboard.\n\n— The Reuni team"
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"Failed to send partner welcome email: {e}")

        flash("Partner account created. You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("partner/invite_register.html", token=token, university_domain=university_domain)


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("3 per hour", key_func=lambda: request.form.get('email', '').strip().lower())
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        if email:
            if email.endswith("@deleted.reuni") or email.startswith("deleted_"):
                flash("If an account exists with that email, a reset link has been sent.", "info")
                return redirect(url_for("auth.login"))

            user = User.query.filter_by(email=email).first()
            if user and user.is_verified and user.deletion_pending_until is None:
                token = generate_password_reset_token(user.email, user.password_hash, current_app.config["SECRET_KEY"])
                reset_url = url_for("auth.reset_password", token=token, _external=True)
                
                msg = Message(
                    subject="Password reset for your Reuni account",
                    recipients=[email]
                )
                msg.body = f"""Hi {user.name},

We received a request to reset the password for your Reuni account.

Click the link below to set a new password. This link expires in 1 hour.

{reset_url}

If you didn't request a password reset, you can safely ignore this email.
Your password will not change unless you click the link above.

— The Reuni team"""
                try:
                    mail.send(msg)
                except Exception as e:
                    current_app.logger.warning(f"Failed to send password reset email to {email}: {e}")

        flash("If an account exists with that email, a reset link has been sent.", "info")
        return redirect(url_for("auth.login"))

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
        if len(new_password) < min_pw_len:
            flash(f"Password must be at least {min_pw_len} characters long.", "danger")
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
            flash("Password updated. You can now log in.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during password reset: {e}")
            flash("An error occurred. Please try again.", "danger")
            return render_template("auth/reset_password.html", token=token)

    session['reset_token'] = token
    return render_template("auth/reset_password.html", token=token)




