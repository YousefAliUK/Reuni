"""
Reuni — Items Routes (Blueprint)
Handles listing, viewing, editing, deleting, buying/claiming items,
and the PIN-handshake flow for completing transactions.
"""

import os
import uuid
import secrets
from datetime import datetime, timezone, timedelta

from werkzeug.security import generate_password_hash, check_password_hash

from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, jsonify, current_app, abort, session
)
from flask_login import login_required, current_user
from PIL import Image as PILImage
from app.utils.emails import send_email

from app import db, limiter
from app.models import (
    Item, User, CancellationRecord, CATEGORY_WEIGHTS, CATEGORIES, CONDITION_CHOICES,
    ALLOWED_EXTENSIONS, MAX_IMAGE_SIZE,
)
from app.utils.decorators import verified_required
from app.utils.cancellation import (
    calculate_hours_held, get_cancellation_tier,
    get_tier_message_for_canceller, get_tier_message_for_other_party
)

items_bp = Blueprint("items", __name__, url_prefix="/items")


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _allowed_file(filename):
    """Check if the uploaded file has a permitted extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _save_image(file_storage):
    """
    Validate, resize, strip EXIF, and save an uploaded image.
    Returns the saved filename (UUID-based) or None on failure.
    """
    if not file_storage or file_storage.filename == "":
        return None

    if not _allowed_file(file_storage.filename):
        return None

    try:
        img = PILImage.open(file_storage)
        img.verify()
        file_storage.seek(0)
        img = PILImage.open(file_storage)
    except Exception:
        return None

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    img.thumbnail((MAX_IMAGE_SIZE, MAX_IMAGE_SIZE), PILImage.LANCZOS)

    clean_img = PILImage.new(img.mode, img.size)
    clean_img.putdata(list(img.getdata()))

    filename = f"{uuid.uuid4().hex}.jpg"
    upload_dir = os.path.join(current_app.static_folder, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    clean_img.save(os.path.join(upload_dir, filename), "JPEG", quality=85)

    return filename


def _delete_image(filename):
    """Remove an uploaded image from disk."""
    if not filename:
        return
    path = os.path.join(current_app.static_folder, "uploads", filename)
    if os.path.isfile(path):
        os.remove(path)


def cancel_claim(item):
    """Reset all claim-related fields on an item."""
    item.buyer_id = None
    item.pin_code = None
    item.pin_expires_at = None
    item.claimed_at = None
    item.pin_attempts = 0


# ──────────────────────────────────────────────
# Detail Page
# ──────────────────────────────────────────────

@items_bp.route("/<int:item_id>")
def detail(item_id):
    """Display the full detail page for an item."""
    item = db.get_or_404(Item, item_id)
    has_cancelled_before = False
    if current_user.is_authenticated:
        has_cancelled_before = CancellationRecord.query.filter_by(
            item_id=item.id,
            cancelled_by_id=current_user.id,
            cancelled_by_role="buyer"
        ).first() is not None
    return render_template("items/detail.html", item=item, has_cancelled_before=has_cancelled_before)


# ──────────────────────────────────────────────
# Create (List an Item)
# ──────────────────────────────────────────────

@items_bp.route("/new", methods=["GET", "POST"])
@login_required
@verified_required
def list_item():
    """Display and process the 'List an Item' form."""
    if not current_user.phone_number:
        flash(
            "Please add a phone number in Settings before listing or buying items. "
            "It is required for the PIN handshake.",
            "warning"
        )
        return redirect(url_for("settings"))
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "")
        condition = request.form.get("condition", "")
        is_free = request.form.get("is_free") == "on"

        # Safe price parsing
        if is_free:
            price = 0.0
        else:
            try:
                price = float(request.form.get("price", 0))
            except (ValueError, TypeError):
                flash("Please enter a valid price.", "danger")
                return redirect(url_for("items.list_item"))
            if price < 0:
                flash("Price cannot be negative.", "danger")
                return redirect(url_for("items.list_item"))

        if not title or category not in CATEGORIES or condition not in CONDITION_CHOICES:
            flash("Please fill in all required fields correctly.", "danger")
            return redirect(url_for("items.list_item"))

        # Input length validation
        if len(title) > 140:
            flash("Title must be 140 characters or fewer.", "danger")
            return redirect(url_for("items.list_item"))
        if len(description) > 2000:
            flash("Description must be 2000 characters or fewer.", "danger")
            return redirect(url_for("items.list_item"))

        image_file = request.files.get("image")
        image_filename = _save_image(image_file)

        if not image_filename:
            flash("Please upload a valid photo of your item (JPG, PNG, or WebP).", "danger")
            return redirect(url_for("items.list_item"))

        kg = CATEGORY_WEIGHTS.get(category, 1.0)

        item = Item(
            title=title,
            description=description,
            category=category,
            condition=condition,
            price=price,
            is_free=is_free,
            image_filename=image_filename,
            kg_saved=kg,
            seller_id=current_user.id,
            university_domain=current_user.university_domain,
        )
        db.session.add(item)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during list_item: {e}")
            flash("A database error occurred. Your item could not be listed. Please try again.", "danger")
            return redirect(url_for("items.list_item"))

        flash(
            f"Item listed. You'll save {kg} kg from landfill when this "
            f"{category.lower()} item finds a new home.",
            "success",
        )
        return redirect(url_for("items.detail", item_id=item.id))

    return render_template(
        "items/list_item.html",
        categories=CATEGORIES,
        conditions=CONDITION_CHOICES,
        category_weights=CATEGORY_WEIGHTS,
    )


# ──────────────────────────────────────────────
# Edit
# ──────────────────────────────────────────────

@items_bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def edit_item(item_id):
    """Edit an existing item listing."""
    item = db.get_or_404(Item, item_id)

    if item.seller_id != current_user.id:
        flash("You can only edit your own items.", "danger")
        return redirect(url_for("index"))

    if item.is_sold:
        flash("You can't edit an item that has already been sold.", "info")
        return redirect(url_for("items.detail", item_id=item.id))

    if item.buyer_id and not item.is_sold:
        flash("You can't edit this item while a handshake is pending.", "info")
        return redirect(url_for("items.detail", item_id=item.id))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "")
        condition = request.form.get("condition", "")
        is_free = request.form.get("is_free") == "on"

        # Safe price parsing
        if is_free:
            price = 0.0
        else:
            try:
                price = float(request.form.get("price", 0))
            except (ValueError, TypeError):
                flash("Please enter a valid price.", "danger")
                return redirect(url_for("items.edit_item", item_id=item.id))
            if price < 0:
                flash("Price cannot be negative.", "danger")
                return redirect(url_for("items.edit_item", item_id=item.id))

        if not title or category not in CATEGORIES or condition not in CONDITION_CHOICES:
            flash("Please fill in all required fields correctly.", "danger")
            return redirect(url_for("items.edit_item", item_id=item.id))

        # Input length validation
        if len(title) > 140:
            flash("Title must be 140 characters or fewer.", "danger")
            return redirect(url_for("items.edit_item", item_id=item.id))
        if len(description) > 2000:
            flash("Description must be 2000 characters or fewer.", "danger")
            return redirect(url_for("items.edit_item", item_id=item.id))

        # Handle optional image replacement
        image_file = request.files.get("image")
        old_image_filename = None
        new_image_filename = None
        if image_file and image_file.filename:
            new_filename = _save_image(image_file)
            if new_filename:
                old_image_filename = item.image_filename
                new_image_filename = new_filename
                item.image_filename = new_filename
            else:
                flash("Invalid image file. Original image kept.", "warning")

        item.title = title
        item.description = description
        item.category = category
        item.condition = condition
        item.price = price
        item.is_free = is_free
        item.kg_saved = CATEGORY_WEIGHTS.get(category, 1.0)

        try:
            db.session.commit()
            if old_image_filename:
                _delete_image(old_image_filename)
        except Exception as e:
            if new_image_filename:
                _delete_image(new_image_filename)
            db.session.rollback()
            current_app.logger.error(f"Database error during edit_item: {e}")
            flash("A database error occurred. Your changes could not be saved. Please try again.", "danger")
            return redirect(url_for("items.edit_item", item_id=item.id))
        flash("Item updated successfully.", "success")
        return redirect(url_for("items.detail", item_id=item.id))

    return render_template(
        "items/edit_item.html",
        item=item,
        categories=CATEGORIES,
        conditions=CONDITION_CHOICES,
        category_weights=CATEGORY_WEIGHTS,
    )


# ──────────────────────────────────────────────
# Delete
# ──────────────────────────────────────────────

@items_bp.route("/<int:item_id>/delete", methods=["POST"])
@login_required
def delete_item(item_id):
    """Delete a listing (only by the seller, only if not sold)."""
    item = db.get_or_404(Item, item_id)

    if item.seller_id != current_user.id:
        flash("You can only delete your own items.", "danger")
        return redirect(url_for("index"))

    if item.is_sold:
        flash("You can't delete an item that has already been sold.", "info")
        return redirect(url_for("items.detail", item_id=item.id))

    if item.buyer_id and not item.is_sold:
        flash("You can't delete this item while a handshake is pending.", "info")
        return redirect(url_for("items.detail", item_id=item.id))

    image_filename = item.image_filename
    db.session.delete(item)
    try:
        db.session.commit()
        _delete_image(image_filename)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error during delete_item: {e}")
        flash("A database error occurred. The item could not be deleted. Please try again.", "danger")
        return redirect(url_for("items.detail", item_id=item.id))

    flash("Item deleted.", "success")
    return redirect(url_for("index"))


# ──────────────────────────────────────────────
# Buy / Claim
# ──────────────────────────────────────────────

@items_bp.route("/<int:item_id>/buy", methods=["POST"])
@login_required
@verified_required
def buy_item(item_id):
    """Initiate a claim — generates a PIN for the handshake."""
    if not current_user.phone_number:
        flash(
            "Please add a phone number in Settings before listing or buying items. "
            "It is required for the PIN handshake.",
            "warning"
        )
        return redirect(url_for("settings"))
    item = db.get_or_404(Item, item_id)

    # Check if this user previously cancelled a claim on this item (anti-griefing)
    has_cancelled_before = CancellationRecord.query.filter_by(
        item_id=item.id,
        cancelled_by_id=current_user.id,
        cancelled_by_role="buyer"
    ).first() is not None

    if has_cancelled_before:
        flash("You cancelled a previous claim on this item. You cannot claim it again.", "danger")
        return redirect(url_for("items.detail", item_id=item.id))

    if item.seller_id == current_user.id:
        flash("You can't buy your own item.", "danger")
        return redirect(url_for("items.detail", item_id=item.id))

    # Atomic claim — prevents race condition when two buyers click simultaneously.
    # The WHERE clause ensures only one concurrent request can succeed.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    pin = f"{secrets.randbelow(10000):04d}"
    hashed_pin = generate_password_hash(pin)
    try:
        rows = Item.query.filter_by(
            id=item_id, buyer_id=None, is_sold=False
        ).update({
            "buyer_id": current_user.id,
            "pin_code": hashed_pin,
            "claimed_at": now,
            "pin_expires_at": now + timedelta(hours=72),
            "pin_attempts": 0,
        }, synchronize_session=False)

        if rows == 0:
            db.session.rollback()
            flash("This item already has a pending claim or has been sold.", "info")
            return redirect(url_for("items.detail", item_id=item.id))

        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error during buy_item: {e}")
        flash("A database error occurred while claiming the item. Please try again.", "danger")
        return redirect(url_for("items.detail", item_id=item.id))

    session[f"pin_{item.id}"] = pin

    try:
        holder = item.seller if item.is_free else current_user
        email_html = f"""<p>Hi {holder.name},</p>
<p>An exchange has been initiated for the item "<strong>{item.title}</strong>" on Reuni.</p>
<p>Your 4-digit transaction PIN is:</p>
<div class="code-block">{pin}</div>
<p>Please keep this PIN secure.</p>
<p>{"Share this PIN with the buyer when they collect the item." if item.is_free else "Show this PIN to the seller after you have inspected the item and confirmed payment."}</p>
<p>— The Reuni team</p>"""
        send_email(
            to_email=holder.email,
            to_name=holder.name,
            subject=f"Transaction PIN for {item.title}",
            html_content=email_html
        )
    except Exception as e:
        current_app.logger.error(f"Failed to send PIN email: {e}")

    flash(f"Claim initiated for \"{item.title}\". Complete the PIN handshake to finish.", "success")
    return redirect(url_for("items.pin_page", item_id=item.id))


# ──────────────────────────────────────────────
# PIN Handshake
# ──────────────────────────────────────────────

@items_bp.route("/<int:item_id>/pin")
@login_required
def pin_page(item_id):
    """Display the PIN handshake page."""
    item = db.get_or_404(Item, item_id)

    # Only buyer or seller can see this page
    if current_user.id != item.buyer_id and current_user.id != item.seller_id:
        flash("You don't have access to this page.", "danger")
        return redirect(url_for("items.detail", item_id=item.id))

    if item.is_sold:
        flash("This transaction is already complete.", "info")
        return redirect(url_for("items.detail", item_id=item.id))

    if not item.pin_code:
        flash("No active claim on this item.", "info")
        return redirect(url_for("items.detail", item_id=item.id))

    # Auto-cancel if expired
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if item.pin_expires_at and now > item.pin_expires_at:
        try:
            cancel_claim(item)
            db.session.commit()
            session.pop(f"pin_{item.id}", None)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during auto-cancel in pin_page: {e}")
        flash("The claim has expired. The item is available again.", "info")
        return redirect(url_for("items.detail", item_id=item.id))

    # Determine who holds the PIN vs who enters it
    # Free items: seller holds PIN, buyer enters
    # Paid items: buyer holds PIN, seller enters
    if item.is_free:
        is_holder = (current_user.id == item.seller_id)
    else:
        is_holder = (current_user.id == item.buyer_id)

    # Get plaintext PIN if cached in session
    pin_code = session.get(f"pin_{item.id}")

    return render_template(
        "items/pin.html",
        item=item,
        is_holder=is_holder,
        pin_code=pin_code,
    )


@items_bp.route("/<int:item_id>/confirm", methods=["POST"])
@login_required
def confirm_pin(item_id):
    """Validate the PIN and complete the transaction."""
    item = db.get_or_404(Item, item_id)

    # Only the entering party can confirm
    if item.is_free:
        allowed = item.buyer_id  # buyer enters for free items
    else:
        allowed = item.seller_id  # seller enters for paid items

    if current_user.id != allowed:
        flash("You are not authorised to confirm this PIN.", "danger")
        return redirect(url_for("items.detail", item_id=item.id))

    if item.is_sold or not item.pin_code:
        flash("No active claim to confirm.", "info")
        return redirect(url_for("items.detail", item_id=item.id))

    # Check expiry
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if item.pin_expires_at and now > item.pin_expires_at:
        try:
            cancel_claim(item)
            db.session.commit()
            session.pop(f"pin_{item.id}", None)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during auto-cancel in confirm_pin: {e}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json or "application/json" in request.accept_mimetypes:
            return jsonify({"success": False, "expired": True, "error": "The claim has expired. The item is available again.", "redirect_url": url_for("items.detail", item_id=item.id)}), 400
        flash("The claim has expired. The item is available again.", "info")
        return redirect(url_for("items.detail", item_id=item.id))

    from werkzeug.security import check_password_hash
    entered_pin = request.form.get("pin", "").strip()

    if not check_password_hash(item.pin_code, entered_pin):
        try:
            item.pin_attempts += 1
            if item.pin_attempts >= 3:
                cancel_claim(item)
                db.session.commit()
                session.pop(f"pin_{item.id}", None)
                if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json or "application/json" in request.accept_mimetypes:
                    return jsonify({"success": False, "cancelled": True, "error": "Too many wrong attempts. The claim has been cancelled.", "redirect_url": url_for("items.detail", item_id=item.id)}), 400
                flash("Too many wrong attempts. The claim has been cancelled.", "danger")
                return redirect(url_for("items.detail", item_id=item.id))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error updating pin attempts: {e}")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json or "application/json" in request.accept_mimetypes:
                return jsonify({"success": False, "error": "A database error occurred. Please try again."}), 500
            flash("A database error occurred. Please try again.", "danger")
            return redirect(url_for("items.pin_page", item_id=item.id))
        remaining = 3 - item.pin_attempts
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json or "application/json" in request.accept_mimetypes:
            return jsonify({"success": False, "error": f"Wrong PIN. {remaining} attempt{'s' if remaining != 1 else ''} remaining.", "remaining_attempts": remaining}), 400
        flash(f"Wrong PIN. {remaining} attempt{'s' if remaining != 1 else ''} remaining.", "danger")
        return redirect(url_for("items.pin_page", item_id=item.id))

    # PIN is correct — complete the transaction
    try:
        item.is_sold = True
        seller = item.seller
        seller.kg_saved_total += item.kg_saved

        # Clear PIN fields
        item.pin_code = None
        item.pin_expires_at = None
        item.claimed_at = None
        item.pin_attempts = 0

        db.session.commit()
        session.pop(f"pin_{item.id}", None)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error during PIN confirmation: {e}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json or "application/json" in request.accept_mimetypes:
            return jsonify({"success": False, "error": "A database error occurred while completing the transaction. Please try again."}), 500
        flash("A database error occurred while completing the transaction. Please try again.", "danger")
        return redirect(url_for("items.pin_page", item_id=item.id))

    if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.is_json or "application/json" in request.accept_mimetypes:
        return jsonify({
            "success": True,
            "kg_saved": item.kg_saved,
            "total_kg": seller.kg_saved_total,
            "redirect_url": url_for("items.detail", item_id=item.id)
        })

    flash(
        f"Handshake complete. \"{item.title}\" is now sold. "
        f"{item.kg_saved} kg saved from landfill.",
        "success",
    )
    return redirect(url_for("items.detail", item_id=item.id))


# ──────────────────────────────────────────────
# Cancel Claim
# ──────────────────────────────────────────────

@items_bp.route("/<int:item_id>/cancel-claim", methods=["POST"])
@login_required
def cancel_claim_route(item_id):
    """Cancel a pending claim — either buyer or seller can do this."""
    item = db.get_or_404(Item, item_id)

    # 1. Check the item is actually in a claimed/pending state
    if item.is_sold:
        flash("This exchange is already complete.", "info")
        return redirect(url_for("items.detail", item_id=item.id))

    if not item.buyer_id or not item.pin_code:
        flash("This item is no longer claimed.", "info")
        return redirect(url_for("items.detail", item_id=item.id))

    # 2. Verify authorization
    if current_user.id != item.buyer_id and current_user.id != item.seller_id:
        abort(403)

    # Data integrity check
    if item.claimed_at is None:
        current_app.logger.error(f"Data integrity issue: claimed_at is None for claimed item {item.id}")
        abort(500)

    # 3. Check auto-expiry
    hours_held = calculate_hours_held(item.claimed_at)
    auto_expiry_hours = current_app.config.get("AUTO_EXPIRY_HOURS", 72)
    if hours_held >= auto_expiry_hours:
        try:
            cancel_claim(item)
            db.session.commit()
            session.pop(f"pin_{item.id}", None)
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during cancel of expired claim: {e}")
        flash("This claim already expired automatically.", "info")
        if current_user.id == item.seller_id:
            return redirect(url_for("items.detail", item_id=item.id))
        else:
            return redirect(url_for("index"))

    # 4. Calculate hours_held and tier
    tier = get_cancellation_tier(item.claimed_at)

    # 5. Determine cancelled_by_role
    if current_user.id == item.buyer_id:
        cancelled_by_role = "buyer"
        other_party_id = item.seller_id
        redirect_url = redirect(url_for("index"))
    else:
        cancelled_by_role = "seller"
        other_party_id = item.buyer_id
        redirect_url = redirect(url_for("items.detail", item_id=item.id))

    other_party = db.session.get(User, other_party_id)
    if not other_party:
        current_app.logger.error(f"Data integrity issue: other party user {other_party_id} not found for claimed item {item.id}")
        abort(500)

    # Cache metadata for email sending
    item_title = item.title
    canceller_name = current_user.name

    # 6. Create the CancellationRecord
    record = CancellationRecord(
        item_id=item.id,
        cancelled_by_id=current_user.id,
        other_party_id=other_party_id,
        claimed_at=item.claimed_at,
        hours_held=hours_held,
        tier=tier,
        cancelled_by_role=cancelled_by_role
    )
    db.session.add(record)

    # 7. Update item status back to available, clear claim fields
    cancel_claim(item)

    # 8. Commit both atomically
    try:
        db.session.commit()
        session.pop(f"pin_{item.id}", None)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error committing cancellation transaction: {e}")
        flash("A database error occurred. Please try again.", "danger")
        return redirect(url_for("items.detail", item_id=item.id))

    # 9. Send email notification to the other party (see email section)
    # Send after db.session.commit() — never inside the transaction
    try:
        other_party_role = "seller" if cancelled_by_role == "buyer" else "buyer"
        tier_msg = get_tier_message_for_other_party(
            tier=tier,
            role=other_party_role,
            name=canceller_name,
            item=item_title,
            hours=hours_held
        )
        item_link = url_for("items.detail", item_id=item_id, _external=True)

        email_html = (
            f"<p>Hello {other_party.name},</p>"
            f"<p>The claim on the item \"<strong>{item_title}</strong>\" has been cancelled.</p>"
            f"<ul class=\"cancellation-list\">"
            f"<li><strong>Cancelled by:</strong> {cancelled_by_role}</li>"
            f"<li><strong>Item name:</strong> {item_title}</li>"
            f"</ul>"
            f"<p>{tier_msg}</p>"
            f"<p>You can view the item listing back on the marketplace here: <a href=\"{item_link}\">{item_link}</a></p>"
            f"<p>— The Reuni team</p>"
        )
        send_email(
            to_email=other_party.email,
            to_name=other_party.name,
            subject=f"A claim on {item_title} has been cancelled",
            html_content=email_html
        )
    except Exception as mail_err:
        current_app.logger.warning(f"Failed to send cancellation email notification to {other_party.email}: {mail_err}")

    # 10. Flash the appropriate tier message to the canceller
    flash_msg = get_tier_message_for_canceller(tier, cancelled_by_role)
    flash(flash_msg, "info" if tier == "clean" else "warning")

    # 11. Redirect to the item page (seller) or browse page (buyer)
    return redirect_url


@items_bp.route("/<int:item_id>/resend-pin", methods=["POST"])
@login_required
@limiter.limit("3 per hour")
def resend_pin(item_id):
    """Regenerate and email a new transaction PIN to the authorized holder."""
    item = db.get_or_404(Item, item_id)

    if current_user.id != item.buyer_id and current_user.id != item.seller_id:
        abort(403)

    if item.is_sold or not item.pin_code:
        flash("No active claim on this item.", "info")
        return redirect(url_for("items.detail", item_id=item.id))

    if item.is_free:
        holder = item.seller
        is_holder = (current_user.id == item.seller_id)
    else:
        holder = item.buyer
        is_holder = (current_user.id == item.buyer_id)

    if not is_holder:
        abort(403)

    from werkzeug.security import generate_password_hash
    pin = f"{secrets.randbelow(10000):04d}"
    item.pin_code = generate_password_hash(pin)
    item.pin_attempts = 0
    try:
        db.session.commit()
        session[f"pin_{item.id}"] = pin
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error during PIN regeneration: {e}")
        flash("A database error occurred. Please try again.", "danger")
        return redirect(url_for("items.pin_page", item_id=item.id))

    try:
        email_html = f"""<p>Hi {holder.name},</p>
<p>A new 4-digit transaction PIN has been generated for "<strong>{item.title}</strong>":</p>
<div class="code-block">{pin}</div>
<p>{"Share this PIN with the buyer when they collect the item." if item.is_free else "Show this PIN to the seller after you have inspected the item and confirmed payment."}</p>
<p>— The Reuni team</p>"""
        send_email(
            to_email=holder.email,
            to_name=holder.name,
            subject=f"New Transaction PIN for {item.title}",
            html_content=email_html
        )
        flash("A new PIN has been generated and sent to your email.", "success")
    except Exception as e:
        current_app.logger.error(f"Failed to send resend-pin email: {e}")
        flash("Failed to send email, but a new PIN was generated. If you can see it on this screen, please note it down.", "warning")

    return redirect(url_for("items.pin_page", item_id=item.id))


# ──────────────────────────────────────────────
# API
# ──────────────────────────────────────────────

@items_bp.route("/api/category-weights")
def category_weights_api():
    """Return the category weights mapping as JSON (used by the Vue component)."""
    return jsonify(CATEGORY_WEIGHTS)
