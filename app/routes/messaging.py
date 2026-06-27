from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from html import escape as html_escape

from app import db, limiter
from app.models import User, Item, Message, Notification
from app.utils.emails import send_message_notification_email
from app.utils.decorators import verified_required
from flask_limiter.util import get_remote_address

messaging_bp = Blueprint("messaging", __name__, url_prefix="/api")




@messaging_bp.route("/messages/<int:item_id>/send", methods=["POST"])
@login_required
@verified_required
@limiter.limit("60 per minute", key_func=get_remote_address)  # Route-level IP spam protection
def send_message(item_id):
    """Send a message to the other party of a claimed item."""
    item = db.get_or_404(Item, item_id)

    # 1. Authorisation: Must be buyer or seller
    if current_user.id != item.buyer_id and current_user.id != item.seller_id:
        return jsonify({"error": "You are not authorised to send messages in this thread."}), 403

    # 2. Claim State Check
    if not item.buyer_id:
        return jsonify({"error": "No active claim exists for this item."}), 400

    if item.is_sold:
        return jsonify({"error": "This transaction has been completed. Chat is read-only."}), 400

    # 3. Message Content Validation
    payload = request.json if request.is_json else request.form
    if not hasattr(payload, "get"):
        return jsonify({"error": "Invalid message payload."}), 400
    raw_content = payload.get("content", "")
    if not isinstance(raw_content, str):
        return jsonify({"error": "Message content must be a string."}), 400
    import re
    content = re.sub(r'[\u200b-\u200d\u2060-\u206f\ufeff\u200e\u200f\u180e]', '', raw_content).strip()
    if not content:
        return jsonify({"error": "Message content cannot be empty."}), 400

    if len(content) > 1000:
        return jsonify({"error": "Message content exceeds the 1,000-character limit."}), 400

    # 4. PIN Substring Filter
    if item.pin_plaintext:
        if item.pin_plaintext in content:
            return jsonify({
                "error": "For security, you cannot share the transaction PIN in chat. If this is a flat or room number, please meet nearby or re-phrase your message."
            }), 400

    # 5. DB Rate Limiting: Max 20 messages per minute per user per thread
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    one_minute_ago = now - timedelta(minutes=1)
    recent_count = Message.query.filter(
        Message.sender_id == current_user.id,
        Message.item_id == item.id,
        Message.created_at >= one_minute_ago
    ).count()
    if recent_count >= 20:
        return jsonify({"error": "Rate limit exceeded. Maximum 20 messages per minute per thread."}), 429

    # Determine recipient
    recipient_id = item.seller_id if current_user.id == item.buyer_id else item.buyer_id
    recipient = db.get_or_404(User, recipient_id)

    # Create message
    message = Message(
        item_id=item.id,
        sender_id=current_user.id,
        recipient_id=recipient_id,
        content=content
    )
    db.session.add(message)

    # Create notification
    notification = Notification(
        user_id=recipient_id,
        title=f"New message from {current_user.name}",
        content=content[:100] + ("..." if len(content) > 100 else ""),
        link=f"/items/{item.id}/pin"
    )
    db.session.add(notification)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error saving message: {e}")
        return jsonify({"error": "A database error occurred. Please try again."}), 500

    # Send email notification asynchronously/outside transaction
    try:
        send_message_notification_email(recipient, current_user, item, content)
    except Exception as email_err:
        current_app.logger.error(f"Error triggering message email notification: {email_err}")

    return jsonify({
        "status": "sent",
        "message": {
            "id": message.id,
            "sender_id": message.sender_id,
            "sender_name": current_user.name,
            "sender_initial": current_user.name[0].upper(),
            "content": content,
            "is_read": message.is_read,
            "created_at": message.created_at.isoformat(),
            "is_mine": True
        }
    }), 201


@messaging_bp.route("/messages/<int:item_id>", methods=["GET"])
@login_required
@verified_required
def poll_messages(item_id):
    """Retrieve all messages for a thread and mark incoming ones as read."""
    item = db.get_or_404(Item, item_id)

    # Authorisation: Must be buyer or seller
    if current_user.id != item.buyer_id and current_user.id != item.seller_id:
        return jsonify({"error": "You are not authorised to view this thread."}), 403

    # Update current user last seen timestamp
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    current_user.last_seen_at = now

    active_buyer_filter = ((Message.sender_id == item.buyer_id) | (Message.recipient_id == item.buyer_id))

    # Retrieve messages with since_id filtering and strict buyer privacy constraints
    since_id = request.args.get("since_id", type=int)
    query = Message.query.filter(
        Message.item_id == item.id,
        active_buyer_filter
    )
    if since_id:
        query = query.filter(Message.id > since_id)
    messages = query.order_by(Message.created_at.asc()).all()

    # Mark only incoming active-buyer messages as read in the database for this thread
    unread_messages = Message.query.filter(
        Message.item_id == item.id,
        Message.recipient_id == current_user.id,
        Message.is_read == False,
        active_buyer_filter
    ).all()

    # Mark all notifications linked to this thread as read
    target_link = f"/items/{item.id}/pin"
    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        link=target_link,
        is_read=False
    ).all()

    for msg in unread_messages:
        msg.is_read = True
    for notif in unread_notifications:
        notif.is_read = True

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error committing poll updates: {e}")

    # Determine thread status
    if item.is_sold:
        thread_status = "sold"
    elif not item.buyer_id:
        thread_status = "cancelled"
    else:
        thread_status = "active"

    messages_json = []
    for msg in messages:
        sender_name = msg.sender.name if msg.sender else "Deleted User"
        messages_json.append({
            "id": msg.id,
            "sender_id": msg.sender_id,
            "sender_name": sender_name,
            "sender_initial": sender_name[0].upper(),
            "content": msg.content,
            "is_read": msg.is_read,
            "created_at": msg.created_at.isoformat(),
            "is_mine": (msg.sender_id == current_user.id)
        })

    # Retrieve all read messages sent by current user in this thread to update read receipts
    seen_messages = Message.query.filter(
        Message.item_id == item.id,
        Message.sender_id == current_user.id,
        Message.is_read == True,
        active_buyer_filter
    ).all()
    seen_ids = [msg.id for msg in seen_messages]

    return jsonify({
        "thread_status": thread_status,
        "messages": messages_json,
        "seen_ids": seen_ids
    }), 200


@messaging_bp.route("/notifications/unread-count", methods=["GET"])
@login_required
@verified_required
def unread_notifications_count():
    """Lightweight endpoint to fetch unread notification counts."""
    # Update current user last seen timestamp
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    current_user.last_seen_at = now
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()

    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({"count": count}), 200


@messaging_bp.route("/notifications", methods=["GET"])
@login_required
@verified_required
def list_notifications():
    """Retrieve the latest 20 notifications for the current user."""
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(20).all()
    
    notifications_json = []
    for notif in notifications:
        notifications_json.append({
            "id": notif.id,
            "title": notif.title,
            "content": notif.content,
            "link": notif.link,
            "is_read": notif.is_read,
            "created_at": notif.created_at.isoformat()
        })
        
    return jsonify(notifications_json), 200


@messaging_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
@verified_required
def mark_notification_read(notification_id):
    """Mark a specific notification as read."""
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first()
    if notification is None:
        return jsonify({"error": "Notification not found."}), 404

    notification.is_read = True

    # Mark sibling notifications with the same link as read
    if notification.link:
        siblings = Notification.query.filter_by(
            user_id=current_user.id,
            link=notification.link,
            is_read=False
        ).all()
        for sib in siblings:
            sib.is_read = True

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error marking notification as read: {e}")
        return jsonify({"error": "A database error occurred."}), 500

    return jsonify({"status": "success"}), 200


@messaging_bp.route("/notifications/read-all", methods=["POST"])
@login_required
@verified_required
def mark_all_notifications_read():
    """Mark all unread notifications for the current user as read."""
    unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).all()
    for notif in unread:
        notif.is_read = True
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Database error marking all notifications as read: {e}")
        return jsonify({"error": "A database error occurred."}), 500

    return jsonify({"status": "success"}), 200
