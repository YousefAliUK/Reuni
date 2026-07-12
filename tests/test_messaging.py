import pytest
from datetime import datetime, timezone, timedelta
from app.models import User, Item, Message, Notification
from app import db
from app.routes.messaging import send_message_notification_email
from app.scheduler import purge_old_notifications, purge_old_messages

@pytest.fixture()
def active_claim_item(db_session, sample_item, second_user):
    """Set sample_item to claimed state by second_user (buyer)."""
    sample_item.buyer_id = second_user.id
    sample_item.pin_code = "1234"
    sample_item.claimed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    sample_item.pin_expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=72)
    db_session.session.commit()
    return sample_item

def test_send_message_happy_path(auth_client, second_user, active_claim_item, db_session):
    """Seller (auth_client / sample_user) sends a message to the buyer (second_user)."""
    resp = auth_client.post(
        f"/api/messages/{active_claim_item.id}/send",
        json={"content": "Let's meet at the SU café at 2pm."}
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["status"] == "sent"
    assert data["message"]["content"] == "Let's meet at the SU café at 2pm."
    assert data["message"]["is_mine"] is True

    # Check database
    msg = Message.query.filter_by(item_id=active_claim_item.id).first()
    assert msg is not None
    assert msg.content == "Let's meet at the SU café at 2pm."
    assert msg.sender_id != second_user.id
    assert msg.recipient_id == second_user.id

    # Check notification is created
    notif = Notification.query.filter_by(user_id=second_user.id).first()
    assert notif is not None
    assert "New message" in notif.title
    assert "SU café" in notif.content
    assert notif.link == f"/items/{active_claim_item.id}/pin"

def test_send_message_pin_filter(auth_client, active_claim_item):
    """Attempting to share the plaintext PIN in chat should be blocked."""
    resp = auth_client.post(
        f"/api/messages/{active_claim_item.id}/send",
        json={"content": "Here is the PIN: 1234"}
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert "cannot share the transaction PIN" in data["error"]

def test_send_message_rate_limit(auth_client, active_claim_item, db_session):
    """Sending more than 20 messages in 1 minute should trigger rate limiting."""
    # Seed 20 messages in the last 10 seconds
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for i in range(20):
        msg = Message(
            item_id=active_claim_item.id,
            sender_id=active_claim_item.seller_id,
            recipient_id=active_claim_item.buyer_id,
            content=f"Spam message {i}",
            created_at=now - timedelta(seconds=i)
        )
        db_session.session.add(msg)
    db_session.session.commit()

    resp = auth_client.post(
        f"/api/messages/{active_claim_item.id}/send",
        json={"content": "Message 21"}
    )
    assert resp.status_code == 429
    data = resp.get_json()
    assert "Rate limit exceeded" in data["error"]

def test_send_message_terminal_state_sold(auth_client, active_claim_item, db_session):
    """Messages cannot be sent once the transaction is completed (sold)."""
    active_claim_item.is_sold = True
    db_session.session.commit()

    resp = auth_client.post(
        f"/api/messages/{active_claim_item.id}/send",
        json={"content": "Item sold already."}
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert "read-only" in data["error"]

def test_send_message_unauthorized(client, second_user, active_claim_item, db_session):
    """Users who are not parties to the claim cannot send messages."""
    # Create third user
    third_user = User(email="third@university.ac.uk", name="Third User", is_verified=True, university_domain="university.ac.uk")
    third_user.set_password("StrongPass123")
    db_session.session.add(third_user)
    db_session.session.commit()

    # Log in as third user
    client.post("/auth/login", data={"email": "third@university.ac.uk", "password": "StrongPass123"}, follow_redirects=True)

    resp = client.post(
        f"/api/messages/{active_claim_item.id}/send",
        json={"content": "Impersonator typing."}
    )
    assert resp.status_code == 403

def test_send_message_content_too_long(auth_client, active_claim_item):
    """Messages longer than 1,000 characters are rejected."""
    long_content = "x" * 1001
    resp = auth_client.post(
        f"/api/messages/{active_claim_item.id}/send",
        json={"content": long_content}
    )
    assert resp.status_code == 400
    data = resp.get_json()
    assert "exceeds" in data["error"]

def test_send_message_empty_content(auth_client, active_claim_item):
    """Empty messages are rejected."""
    resp = auth_client.post(
        f"/api/messages/{active_claim_item.id}/send",
        json={"content": "   "}
    )
    assert resp.status_code == 400

def test_poll_messages_marks_as_read(client, second_user, active_claim_item, db_session):
    """Polling messages returns list and marks incoming messages as read."""
    # Seller sends message
    msg = Message(
        item_id=active_claim_item.id,
        sender_id=active_claim_item.seller_id,
        recipient_id=second_user.id,
        content="Hello!",
        is_read=False
    )
    db_session.session.add(msg)
    db_session.session.commit()

    # Log in as buyer (second_user)
    client.post("/auth/login", data={"email": "other@university.ac.uk", "password": "StrongPass123"}, follow_redirects=True)

    resp = client.get(f"/api/messages/{active_claim_item.id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["thread_status"] == "active"
    assert len(data["messages"]) == 1
    assert data["messages"][0]["content"] == "Hello!"
    assert data["messages"][0]["is_mine"] is False

    # Verify message is marked read in DB
    db_session.session.refresh(msg)
    assert msg.is_read is True

def test_notifications_unread_count_and_list(client, second_user, active_claim_item, db_session):
    """Test unread count, list, read notification endpoints."""
    # Log in as buyer (second_user)
    client.post("/auth/login", data={"email": "other@university.ac.uk", "password": "StrongPass123"}, follow_redirects=True)

    notif = Notification(user_id=second_user.id, title="Test Notif", content="Test Body", link="/", is_read=False)
    db_session.session.add(notif)
    db_session.session.commit()

    # Unread count
    resp_cnt = client.get("/api/notifications/unread-count")
    assert resp_cnt.status_code == 200
    assert resp_cnt.get_json()["count"] == 1

    # List notifications
    resp_lst = client.get("/api/notifications")
    assert resp_lst.status_code == 200
    data_lst = resp_lst.get_json()
    assert len(data_lst) == 1
    assert data_lst[0]["title"] == "Test Notif"

    # Mark read
    resp_rd = client.post(f"/api/notifications/{notif.id}/read")
    assert resp_rd.status_code == 200
    assert db_session.session.query(Notification).filter_by(id=notif.id).first().is_read is True

    # Mark all read
    notif2 = Notification(user_id=second_user.id, title="Notif 2", content="Body 2", link="/", is_read=False)
    db_session.session.add(notif2)
    db_session.session.commit()
    resp_rd_all = client.post("/api/notifications/read-all")
    assert resp_rd_all.status_code == 200
    assert db_session.session.query(Notification).filter_by(id=notif2.id).first().is_read is True

def test_email_notification_cooldown_and_online(client, second_user, active_claim_item, db_session, app):
    """Test that email notification is sent or skipped according to cooldown & online status."""
    with app.app_context():
        # Seller (sample_user) is sender, buyer (second_user) is recipient
        db_recipient = db.session.get(User, second_user.id)
        db_sender = db.session.get(User, active_claim_item.seller_id)
        db_item = db.session.get(Item, active_claim_item.id)

        # Clear outbox
        from app.utils.emails import outbox
        outbox.clear()

        # Case A: Recipient is online (<30s) -> Email skipped
        db_recipient.last_seen_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=15)
        db.session.commit()
        send_message_notification_email(db_recipient, db_sender, db_item, "Hi online!")
        assert len(outbox) == 0

        # Case B: Recipient is offline (>30s) -> Email sent
        db_recipient.last_seen_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=45)
        db.session.commit()
        send_message_notification_email(db_recipient, db_sender, db_item, "Hi offline!")
        assert len(outbox) == 1
        assert "New message from Test User" in outbox[0].subject

        # Record notification to simulate the first send cooldown trigger
        notif = Notification(
            user_id=db_recipient.id,
            title=f"New message from {db_sender.name}",
            content="Hi offline!",
            link=f"/items/{db_item.id}/pin",
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        db.session.add(notif)
        db.session.commit()

        # Case C: Cooldown active (<5 minutes since last notification) -> Email skipped
        outbox.clear()
        send_message_notification_email(db_recipient, db_sender, db_item, "Hi cooldown!")
        assert len(outbox) == 0

def test_gdpr_anonymisation_replaces_message_content(client, second_user, active_claim_item, db_session):
    """GDPR erasure deletes user notifications and anonymises message content, keeping metadata."""
    # Seller sends message
    msg = Message(
        item_id=active_claim_item.id,
        sender_id=active_claim_item.seller_id,
        recipient_id=second_user.id,
        content="Secret message containing PII."
    )
    db_session.session.add(msg)
    
    # Seller has notification
    notif = Notification(
        user_id=active_claim_item.seller_id,
        title="Alert",
        content="Test GDPR"
    )
    db_session.session.add(notif)
    db_session.session.commit()
    notif_id = notif.id

    # Seller deletes account
    seller = db_session.session.get(User, active_claim_item.seller_id)
    seller.anonymise()
    db_session.session.commit()

    # Verify message content anonymised
    db_session.session.refresh(msg)
    assert msg.content == "[Message removed — account deleted]"
    assert msg.sender_id == seller.id

    # Verify notification deleted
    assert db_session.session.get(Notification, notif_id) is None

def test_scheduler_purge_notifications_and_messages(client, second_user, active_claim_item, db_session, app):
    """Test nightly database cleanup purges read/old notifications and old inactive messages."""
    with app.app_context():
        # Setup notifications
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        # Read & 31 days old -> Deleted
        notif_read_old = Notification(user_id=second_user.id, title="1", is_read=True, created_at=now - timedelta(days=31))
        # Unread & 31 days old -> Kept
        notif_unread_old = Notification(user_id=second_user.id, title="2", is_read=False, created_at=now - timedelta(days=31))
        # Unread & 91 days old -> Deleted
        notif_all_old = Notification(user_id=second_user.id, title="3", is_read=False, created_at=now - timedelta(days=91))
        
        # Setup messages
        # Active claim & 91 days old -> Kept (not sold or deleted)
        msg_active_old = Message(item_id=active_claim_item.id, sender_id=active_claim_item.seller_id, recipient_id=second_user.id, content="Active", created_at=now - timedelta(days=91))
        
        # Inactive claim (deleted item) & 91 days old -> Deleted
        inactive_item = Item(
            title="Unclaimed Item",
            description="Desc",
            price=5.0,
            is_free=False,
            seller_id=active_claim_item.seller_id,
            category="Textbooks",
            condition="New",
            university_domain="university.ac.uk",
            buyer_id=None,
            is_deleted=True
        )
        db.session.add(inactive_item)
        db.session.commit()

        msg_inactive_old = Message(item_id=inactive_item.id, sender_id=active_claim_item.seller_id, recipient_id=second_user.id, content="Inactive", created_at=now - timedelta(days=91))

        db.session.add_all([notif_read_old, notif_unread_old, notif_all_old, msg_active_old, msg_inactive_old])
        db.session.commit()

        # Save IDs after commit
        notif_read_old_id = notif_read_old.id
        notif_unread_old_id = notif_unread_old.id
        notif_all_old_id = notif_all_old.id
        msg_active_old_id = msg_active_old.id
        msg_inactive_old_id = msg_inactive_old.id

        # Run scheduler purge jobs
        purge_old_notifications(app)
        purge_old_messages(app)

        # Force SQLAlchemy to expire identity maps and refresh from DB
        db.session.expire_all()

        # Assertions
        assert db.session.query(Notification).filter_by(id=notif_read_old_id).first() is None
        assert db.session.query(Notification).filter_by(id=notif_unread_old_id).first() is not None
        assert db.session.query(Notification).filter_by(id=notif_all_old_id).first() is None
        assert db.session.query(Message).filter_by(id=msg_active_old_id).first() is not None
        assert db.session.query(Message).filter_by(id=msg_inactive_old_id).first() is None


def test_messaging_payload_validation_hardening(client, sample_user, active_claim_item):
    """Test that malformed JSON payloads or non-string content values are rejected with 400."""
    # Log in as seller (sample_user)
    client.post("/auth/login", data={"email": "test@university.ac.uk", "password": "StrongPass123"}, follow_redirects=True)

    # 1. Non-dict/array payload
    resp = client.post(f"/api/messages/{active_claim_item.id}/send", json=["content", "hello"])
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Invalid message payload."

    # 2. Non-string content field
    resp = client.post(f"/api/messages/{active_claim_item.id}/send", json={"content": 12345})
    assert resp.status_code == 400
    assert resp.get_json()["error"] == "Message content must be a string."


def test_notification_id_enumeration_mitigation(client, sample_user, second_user, db_session):
    """Test that unauthorized notifications return 404 instead of 403 to prevent ID enumeration."""
    # Create notification for second_user (buyer)
    notif = Notification(user_id=second_user.id, title="Secret", content="Private", link="/", is_read=False)
    db_session.session.add(notif)
    db_session.session.commit()

    # Log in as S (sample_user)
    client.post("/auth/login", data={"email": "test@university.ac.uk", "password": "StrongPass123"}, follow_redirects=True)

    # Attempt to read someone else's notification
    resp = client.post(f"/api/notifications/{notif.id}/read")
    assert resp.status_code == 404
    assert resp.get_json()["error"] == "Notification not found."


def test_active_buyer_query_isolation(client, sample_user, second_user, active_claim_item, db_session):
    """Test that cancelling a claim and claiming with a new buyer isolates chat polls/unread updates."""
    # Log in as seller (sample_user)
    client.post("/auth/login", data={"email": "test@university.ac.uk", "password": "StrongPass123"}, follow_redirects=True)

    # Send message S -> B1 (second_user)
    resp = client.post(f"/api/messages/{active_claim_item.id}/send", json={"content": "Hello B1!"})
    assert resp.status_code == 201
    msg = db_session.session.query(Message).first()
    assert msg.is_read is False

    # Cancel the claim
    client.post(f"/items/{active_claim_item.id}/cancel-claim", follow_redirects=True)
    db_session.session.refresh(active_claim_item)
    assert active_claim_item.buyer_id is None

    # Create third user (B2)
    from app.models import User
    third_user = User(
        name="Third User",
        email="third@university.ac.uk",
        university_domain="university.ac.uk",
        is_verified=True,
        is_active=True
    )
    third_user.set_password("StrongPass123")
    db_session.session.add(third_user)
    db_session.session.commit()

    # Third user claims the item
    client.post("/auth/logout", follow_redirects=True)
    client.post("/auth/login", data={"email": "third@university.ac.uk", "password": "StrongPass123"}, follow_redirects=True)
    client.post(f"/items/{active_claim_item.id}/buy", follow_redirects=True)

    db_session.session.refresh(active_claim_item)
    assert active_claim_item.buyer_id == third_user.id

    # Verify B2 cannot see S's message to B1 in chat poll
    resp_poll = client.get(f"/api/messages/{active_claim_item.id}")
    assert resp_poll.status_code == 200
    data_poll = resp_poll.get_json()
    assert len(data_poll["messages"]) == 0  # Message S -> B1 is isolated!

    # Verify polling by B2 doesn't mark S -> B1 message as read
    db_session.session.refresh(msg)
    assert msg.is_read is False
