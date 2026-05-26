"""
UniCycle — Items Routes (Blueprint)
Handles listing, viewing, editing, deleting, buying/claiming items,
and the PIN-handshake flow for completing transactions.
"""

import os
import uuid
import secrets
from datetime import datetime, timezone, timedelta

from flask import (
    Blueprint, render_template, redirect, url_for, flash,
    request, jsonify, current_app,
)
from flask_login import login_required, current_user
from PIL import Image as PILImage

from app import db
from app.models import (
    Item, CATEGORY_WEIGHTS, CATEGORIES, CONDITION_CHOICES,
    ALLOWED_EXTENSIONS, MAX_IMAGE_SIZE,
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


def _cancel_claim(item):
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
    return render_template("items/detail.html", item=item)


# ──────────────────────────────────────────────
# Create (List an Item)
# ──────────────────────────────────────────────

@items_bp.route("/new", methods=["GET", "POST"])
@login_required
def list_item():
    """Display and process the 'List an Item' form."""
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
            f"Item listed! You'll save {kg} kg ♻️ from landfill when this "
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
        if image_file and image_file.filename:
            new_filename = _save_image(image_file)
            if new_filename:
                _delete_image(item.image_filename)
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
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during edit_item: {e}")
            flash("A database error occurred. Your changes could not be saved. Please try again.", "danger")
            return redirect(url_for("items.edit_item", item_id=item.id))
        flash("Item updated successfully!", "success")
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

    _delete_image(item.image_filename)
    db.session.delete(item)
    try:
        db.session.commit()
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
def buy_item(item_id):
    """Initiate a claim — generates a PIN for the handshake."""
    item = db.get_or_404(Item, item_id)

    if item.seller_id == current_user.id:
        flash("You can't buy your own item!", "danger")
        return redirect(url_for("items.detail", item_id=item.id))

    # Atomic claim — prevents race condition when two buyers click simultaneously.
    # The WHERE clause ensures only one concurrent request can succeed.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    pin = f"{secrets.randbelow(10000):04d}"
    try:
        rows = Item.query.filter_by(
            id=item_id, buyer_id=None, is_sold=False
        ).update({
            "buyer_id": current_user.id,
            "pin_code": pin,
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

    flash(f"Claim initiated for \"{item.title}\"! Complete the PIN handshake to finish.", "success")
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
            _cancel_claim(item)
            db.session.commit()
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

    return render_template(
        "items/pin.html",
        item=item,
        is_holder=is_holder,
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
            _cancel_claim(item)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error during auto-cancel in confirm_pin: {e}")
        flash("The claim has expired. The item is available again.", "info")
        return redirect(url_for("items.detail", item_id=item.id))

    entered_pin = request.form.get("pin", "").strip()

    if entered_pin != item.pin_code:
        try:
            item.pin_attempts += 1
            if item.pin_attempts >= 3:
                _cancel_claim(item)
                db.session.commit()
                flash("Too many wrong attempts. The claim has been cancelled.", "danger")
                return redirect(url_for("items.detail", item_id=item.id))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Database error updating pin attempts: {e}")
            flash("A database error occurred. Please try again.", "danger")
            return redirect(url_for("items.pin_page", item_id=item.id))
        remaining = 3 - item.pin_attempts
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
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error during PIN confirmation: {e}")
        flash("A database error occurred while completing the transaction. Please try again.", "danger")
        return redirect(url_for("items.pin_page", item_id=item.id))

    flash(
        f"✅ Handshake complete! \"{item.title}\" is now sold. "
        f"{item.kg_saved} kg saved from landfill!",
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

    if current_user.id != item.buyer_id and current_user.id != item.seller_id:
        flash("You don't have permission to cancel this claim.", "danger")
        return redirect(url_for("items.detail", item_id=item.id))

    if item.is_sold:
        flash("This transaction is already complete and cannot be cancelled.", "info")
        return redirect(url_for("items.detail", item_id=item.id))

    if not item.pin_code:
        flash("No active claim to cancel.", "info")
        return redirect(url_for("items.detail", item_id=item.id))

    try:
        _cancel_claim(item)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error during cancel_claim_route: {e}")
        flash("A database error occurred while cancelling the claim. Please try again.", "danger")
        return redirect(url_for("items.detail", item_id=item.id))

    flash(f"Claim on \"{item.title}\" has been cancelled. The item is available again.", "info")
    return redirect(url_for("items.detail", item_id=item.id))


# ──────────────────────────────────────────────
# API
# ──────────────────────────────────────────────

@items_bp.route("/api/category-weights")
def category_weights_api():
    """Return the category weights mapping as JSON (used by the Vue component)."""
    return jsonify(CATEGORY_WEIGHTS)
