from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature

def generate_partner_invite_token(
    university_domain: str,
    secret_key: str,
    max_age_seconds: int = 172800  # 48 hours
) -> str:
    serializer = URLSafeTimedSerializer(secret_key, salt="partner-invite-salt")
    return serializer.dumps(university_domain)

def verify_partner_invite_token(
    token: str,
    secret_key: str,
    max_age_seconds: int = 172800
) -> str | None:
    serializer = URLSafeTimedSerializer(secret_key, salt="partner-invite-salt")
    try:
        return serializer.loads(token, max_age=max_age_seconds)
    except (SignatureExpired, BadSignature):
        return None


def generate_password_reset_token(
    email: str,
    password_hash: str,
    secret_key: str,
    max_age_seconds: int = 3600
) -> str:
    """
    Generates a signed, time-limited password reset token encoding the
    user's email. The current password hash is used as the serializer salt,
    ensuring the token is automatically invalidated once the password changes.
    """
    serializer = URLSafeTimedSerializer(secret_key, salt=password_hash)
    return serializer.dumps(email)


def verify_password_reset_token(
    token: str,
    password_hash: str,
    secret_key: str,
    max_age_seconds: int = 3600
) -> str | None:
    """
    Validates a password reset token. Returns the decoded email string if
    valid, or None if expired or tampered.
    Catches SignatureExpired and BadSignature internally — never raises.
    The password_hash passed here must be the CURRENT hash from the database
    at the time of verification.
    """
    serializer = URLSafeTimedSerializer(secret_key, salt=password_hash)
    try:
        return serializer.loads(token, max_age=max_age_seconds)
    except (SignatureExpired, BadSignature):
        return None

