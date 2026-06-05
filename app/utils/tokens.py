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
