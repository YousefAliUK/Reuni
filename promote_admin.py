"""
promote_admin.py — Development/staging utility to bootstrap or promote an admin account.

USAGE:
    python promote_admin.py <email>
    python promote_admin.py <email> --name "Display Name"

EXAMPLES:
    python promote_admin.py 19284815@brookes.ac.uk
    python promote_admin.py admin@brookes.ac.uk --name "Yousef (Admin)"

SAFETY:
    - Refuses to run unless app.debug is True (prevents accidental production use).
    - Never hardcodes credentials. Generates a cryptographically secure random password
      for new accounts and prints it ONCE to stdout only (never logged via app.logger).
    - Promoting an existing user does not touch their password.
    - university_domain is auto-extracted from the email address using the same
      validation logic as the registration flow.
"""

import argparse
import secrets
import string
import sys

from app import create_app, db
from app.models import User
from app.utils.email_validation import extract_university_domain


def generate_secure_password(length: int = 16) -> str:
    """Generate a cryptographically secure random password."""
    if length < 3:
        raise ValueError("length must be at least 3")
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    # Guarantee at least one of each required character class
    while True:
        pw = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(c.isupper() for c in pw)
            and any(c.islower() for c in pw)
            and any(c.isdigit() for c in pw)
        ):
            return pw


def main():
    parser = argparse.ArgumentParser(
        description="Promote a user to admin or create an admin account. "
                    "Only runs in debug mode to prevent accidental production use."
    )
    parser.add_argument(
        "email",
        help="Email address of the account to promote or create (must be a .ac.uk address)."
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Display name for new accounts (default: 'Admin')."
    )
    args = parser.parse_args()

    app = create_app()

    # ── Production guard ──────────────────────────────────────────────────────
    if not app.debug:
        print(
            "ERROR: Refusing to run promote_admin.py outside of debug mode.\n"
            "This script is for development and staging only.\n"
            "Set DEBUG=True (or use DevelopmentConfig) to run this script.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Domain extraction ─────────────────────────────────────────────────────
    domain = extract_university_domain(args.email)
    if domain is None:
        print(
            f"ERROR: '{args.email}' is not a valid .ac.uk email address.\n"
            "This script only creates accounts for university email domains.",
            file=sys.stderr,
        )
        sys.exit(1)

    display_name = args.name or "Admin"

    with app.app_context():
        existing = User.query.filter_by(email=args.email).first()

        if existing:
            # ── Promote existing user ─────────────────────────────────────────
            old_role = existing.role
            existing.role = "admin"
            existing.is_active = True
            existing.is_verified = True
            db.session.commit()
            print(f"\n✓  User '{args.email}' promoted to admin.")
            if old_role != "admin":
                print(f"   Previous role: {old_role} → admin")
            print("   Password unchanged.\n")
        else:
            # ── Create new admin account ──────────────────────────────────────
            password = generate_secure_password()
            new_user = User(
                email=args.email,
                name=display_name,
                is_verified=True,
                is_active=True,
                role="admin",
                university_domain=domain,
                phone_number=None,
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            print(f"\n✓  New admin account created.")
            print(f"   Email:    {args.email}")
            print(f"   Password: {password}")
            print(
                "\n   ⚠  Save this password now — it will not be shown again.\n"
                "      Change it immediately after first login.\n"
            )


if __name__ == "__main__":
    main()
