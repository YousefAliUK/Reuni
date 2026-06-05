from datetime import datetime, timezone
from flask import current_app

# Tier boundaries in hours — configurable, not hardcoded
LATE_THRESHOLD_HOURS = 24
AUTO_EXPIRY_HOURS = 72  # already exists in config, reference it


def calculate_hours_held(claimed_at: datetime) -> float:
    """
    Returns hours elapsed since claim was made, rounded to 2 decimal places.
    Converts inputs defensively to ensure timezone consistency.
    """
    if claimed_at is None:
        raise ValueError("claimed_at cannot be None")

    # If claimed_at is offset-naive, treat it as UTC
    if claimed_at.tzinfo is None:
        claimed_at = claimed_at.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    diff = now - claimed_at
    hours = diff.total_seconds() / 3600.0
    return round(max(0.0, hours), 2)


def get_cancellation_tier(claimed_at: datetime) -> str:
    """
    Returns 'clean' or 'late' based on how long the claim has been held.
    claimed_at must be timezone-aware UTC.
    """
    # Force timezone-aware UTC defensively if caller passed offset-naive
    if claimed_at is not None and claimed_at.tzinfo is None:
        claimed_at = claimed_at.replace(tzinfo=timezone.utc)

    hours = calculate_hours_held(claimed_at)

    try:
        threshold = current_app.config.get("LATE_THRESHOLD_HOURS", LATE_THRESHOLD_HOURS)
    except RuntimeError:
        threshold = LATE_THRESHOLD_HOURS

    # If exactly threshold (e.g. 24h) or less, it's clean. If greater, it's late.
    if hours <= threshold:
        return "clean"
    else:
        return "late"


def get_tier_message_for_canceller(tier: str, role: str) -> str:
    """
    Returns the flash message shown to the person who initiated the cancellation.
    role is 'buyer' or 'seller'.
    """
    if tier == "clean":
        return "You cancelled this claim. The item has been returned to the marketplace."
    else:
        try:
            threshold = current_app.config.get("LATE_THRESHOLD_HOURS", LATE_THRESHOLD_HOURS)
        except RuntimeError:
            threshold = LATE_THRESHOLD_HOURS
        return f"You cancelled this claim after {threshold} hours. This has been recorded and may affect your reputation score in the future."


def get_tier_message_for_other_party(tier: str, role: str, name: str = "[Name]", item: str = "[Item]", hours: float = 0.0) -> str:
    """
    Returns the flash message shown to the other party via email.
    role is the role of the OTHER party (not the canceller).
    """
    if tier == "clean":
        return f"{name} cancelled their claim on {item}. It's back on the marketplace."
    else:
        return f"{name} cancelled their claim on {item} after holding it for {hours} hours. It has been returned to the marketplace."
