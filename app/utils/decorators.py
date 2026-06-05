from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

def verified_required(f):
    """
    Use this decorator on any route that requires a verified account.
    Stack it BELOW @login_required:
    
    @app.route('/listings/new')
    @login_required
    @verified_required
    def new_listing():
        ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_verified:
            flash("Please verify your email to access this feature.", "warning")
            return redirect(url_for("auth.resend_verification"))
        return f(*args, **kwargs)
    return decorated_function

def partner_required(f):
    """
    Requires the current user to have role 'partner' or 'admin'.
    Stack BELOW @login_required.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ("partner", "admin"):
            flash("You do not have permission to access the partner dashboard.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """
    Requires the current user to have role 'admin'.
    Stack BELOW @login_required.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

