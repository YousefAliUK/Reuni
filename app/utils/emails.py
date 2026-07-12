from flask import current_app
from markupsafe import escape
from brevo import Brevo
from brevo.transactional_emails import SendTransacEmailRequestSender, SendTransacEmailRequestToItem
from brevo.core.api_error import ApiError

# Outbox for tracking emails during tests
outbox = []

def wrap_in_brand_template(subject: str, to_name: str, inner_content_html: str) -> str:
    """
    Wraps the inner HTML content in a beautiful, responsive, single-column brand envelope.
    Follows Reuni's elite design token system palette.
    """
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(subject)}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background-color: #FAF7F2;
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            color: #1C1917;
            -webkit-font-smoothing: antialiased;
        }}
        .email-wrapper {{
            width: 100%;
            background-color: #FAF7F2;
            padding: 40px 0;
            box-sizing: border-box;
        }}
        .email-card {{
            max-width: 540px;
            margin: 0 auto;
            background-color: #FFFFFF;
            border-radius: 12px;
            border: 1px solid rgba(28, 25, 23, 0.12);
            border-top: 4px solid #0F766E;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
            overflow: hidden;
        }}
        .email-header {{
            padding: 32px 32px 20px 32px;
            border-bottom: 1px solid rgba(28, 25, 23, 0.06);
        }}
        .logo-text {{
            font-size: 20px;
            font-weight: 700;
            color: #1C1917;
            display: inline-block;
            vertical-align: middle;
            margin: 0;
        }}
        .email-body {{
            padding: 32px;
            font-size: 15px;
            line-height: 1.65;
            color: #44403C;
        }}
        .email-body p {{
            margin-top: 0;
            margin-bottom: 16px;
        }}
        .email-body p:last-child {{
            margin-bottom: 0;
        }}
        .email-footer {{
            padding: 0 32px 40px 32px;
            text-align: center;
            font-size: 12px;
            color: #706A64;
            line-height: 1.5;
        }}
        .email-footer p {{
            margin: 0 0 8px 0;
        }}
        .email-footer p:last-child {{
            margin-bottom: 0;
        }}
        .email-footer a {{
            color: #0F766E;
            text-decoration: none;
        }}
        .email-footer a:hover {{
            text-decoration: underline;
        }}
        /* Unified Template Utility Classes */
        .btn-primary {{
            display: inline-block;
            padding: 12px 24px;
            font-size: 14px;
            font-weight: 600;
            color: #FFFFFF !important;
            background-color: #0F766E;
            text-decoration: none;
            border-radius: 8px;
            margin: 16px 0;
            text-align: center;
        }}
        .code-block {{
            background-color: #F4F0E8;
            border-radius: 8px;
            padding: 18px;
            text-align: center;
            margin: 24px 0;
            font-family: 'JetBrains Mono', 'Fira Code', Monaco, Consolas, monospace;
            font-size: 28px;
            font-weight: 800;
            letter-spacing: 6px;
            color: #0F766E;
            border: 1px solid rgba(28, 25, 23, 0.06);
        }}
        .cancellation-list {{
            background-color: #F4F0E8;
            border-radius: 8px;
            padding: 16px 16px 16px 36px;
            margin: 20px 0;
            list-style-type: disc;
        }}
        .cancellation-list li {{
            margin-bottom: 8px;
            color: #44403C;
        }}
        .cancellation-list li:last-child {{
            margin-bottom: 0;
        }}
        a {{
            color: #0F766E;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="email-wrapper">
        <div class="email-card">
            <div class="email-header">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#0F766E" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="display: inline-block; vertical-align: middle; margin-right: 8px;">
                    <polyline points="23 4 23 10 17 10"></polyline>
                    <polyline points="1 20 1 14 7 14"></polyline>
                    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
                </svg>
                <span class="logo-text">Reuni</span>
            </div>
            <div class="email-body">
                {inner_content_html}
            </div>
            <div class="email-footer">
                <p>Sent by Reuni — Oxford Brookes Student Circular Economy</p>
                <p>© 2026 Reuni. All rights reserved.</p>
            </div>
        </div>
    </div>
</body>
</html>
"""

def send_email(to_email: str, to_name: str, subject: str, html_content: str) -> bool:
    """
    Sends an email using the Brevo API client.
    Respects MAIL_SUPPRESS_SEND config option for unit testing and local development.
    Returns True if successful (or suppressed), False otherwise.
    """
    # Wrap in our premium brand envelope
    full_html = wrap_in_brand_template(subject, to_name, html_content)

    # If testing or MAIL_SUPPRESS_SEND is enabled, record to mock outbox and bypass API
    if current_app.config.get("TESTING") or current_app.config.get("MAIL_SUPPRESS_SEND"):
        class MockMessage:
            def __init__(self, recipient, recipient_name, subject_line, content):
                self.recipients = [recipient]
                self.to_name = recipient_name
                self.subject = subject_line
                self.html_content = content
                self.body = content  # Keep compatibility with existing .body checks in tests
        
        outbox.append(MockMessage(to_email, to_name, subject, full_html))
        return True

    api_key = current_app.config.get("BREVO_API_KEY")
    if not api_key:
        current_app.logger.warning("Brevo API key (BREVO_API_KEY) is not set; skipping email send")
        return False

    try:
        timeout_val = float(current_app.config.get("MAIL_TIMEOUT", 30))
    except (ValueError, TypeError):
        timeout_val = 30.0
    client = Brevo(api_key=api_key, timeout=timeout_val)
    sender_email = current_app.config.get("BREVO_SENDER_EMAIL", "support@reuni.ac.uk")
    
    try:
        client.transactional_emails.send_transac_email(
            sender=SendTransacEmailRequestSender(email=sender_email, name="Reuni"),
            to=[SendTransacEmailRequestToItem(email=to_email, name=to_name)],
            subject=subject,
            html_content=full_html,
        )
        return True
    except ApiError as e:
        current_app.logger.error(f"Brevo API error sending email: {e}")
        return False
    except Exception as e:
        current_app.logger.error(f"Unexpected error sending email: {e}")
        return False


def send_message_notification_email(recipient, sender, item, message_content):
    """
    Sends an email notification via Brevo if recipient is not online and
    no other message notification email was sent for this thread in the last 5 minutes.
    """
    from datetime import datetime, timezone, timedelta
    from app.models import Notification
    from flask import request, has_request_context

    # 1. Skip if recipient was online in the last 30 seconds
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if recipient.last_seen_at and (now - recipient.last_seen_at).total_seconds() < 30:
        return False

    # 2. Skip if email sent in the last 5 minutes (cooldown)
    five_minutes_ago = now - timedelta(minutes=5)
    recent_notif = Notification.query.filter(
        Notification.user_id == recipient.id,
        Notification.link == f"/items/{item.id}/pin",
        Notification.title.like("New message from%"),
        Notification.created_at >= five_minutes_ago
    ).first()
    if recent_notif:
        return False

    # 3. Send the email
    safe_sender_name = escape(sender.name)
    safe_item_title = escape(item.title)
    safe_preview = escape(message_content[:100] + ("..." if len(message_content) > 100 else ""))
    
    # Construct host and scheme securely from BASE_URL to prevent Host Header Injection in emails
    base_url = current_app.config.get("BASE_URL") or "http://localhost:5000"
    from urllib.parse import urlsplit
    base_parsed = urlsplit(base_url)
    scheme = base_parsed.scheme or "http"
    base_host = base_parsed.netloc or "localhost:5000"

    # Prepend subdomain of recipient if available
    uni_domain = recipient.university_domain
    subdomain = None
    if uni_domain:
        uni_map = current_app.config.get("SUBDOMAIN_UNIVERSITY_MAP", {})
        rev_map = {v: k for k, v in uni_map.items()}
        subdomain = rev_map.get(uni_domain)

    if subdomain and base_host != "localhost:5000" and not base_host.endswith(".localhost"):
        parts = base_host.split('.')
        if len(parts) >= 3 and (
            (parts[-2] == "ac" and parts[-1] == "uk") or 
            (parts[-2] == "co" and parts[-1] == "uk")
        ):
            base_domain = '.'.join(parts[-3:])
        elif len(parts) >= 2:
            base_domain = '.'.join(parts[-2:])
        else:
            base_domain = base_host
        host = f"{subdomain}.{base_domain}"
    else:
        host = base_host

    email_html = f"""<p>Hi {escape(recipient.name)},</p>
<p>You have a new message from <strong>{safe_sender_name}</strong> regarding the item "<strong>{safe_item_title}</strong>" on Reuni:</p>
<blockquote style="border-left: 4px solid #0F766E; padding-left: 16px; margin: 16px 0; color: #44403C; font-style: italic;">
    {safe_preview}
</blockquote>
    <a href="{scheme}://{host}/items/{item.id}/pin" class="btn-primary">
        Reply in Chat
    </a>
<p>— The Reuni team</p>"""
    
    return send_email(
        to_email=recipient.email,
        to_name=recipient.name,
        subject=f"New message from {sender.name} - Reuni",
        html_content=email_html
    )
