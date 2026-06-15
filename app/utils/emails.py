from flask import current_app
from brevo import Brevo
from brevo.transactional_emails import SendTransacEmailRequestSender, SendTransacEmailRequestToItem
from brevo.core.api_error import ApiError

# Outbox for tracking emails during tests
outbox = []

def send_email(to_email: str, to_name: str, subject: str, html_content: str) -> bool:
    """
    Sends an email using the Brevo API client.
    Respects MAIL_SUPPRESS_SEND config option for unit testing and local development.
    Returns True if successful (or suppressed), False otherwise.
    """
    # If testing or MAIL_SUPPRESS_SEND is enabled, record to mock outbox and bypass API
    if current_app.config.get("TESTING") or current_app.config.get("MAIL_SUPPRESS_SEND"):
        class MockMessage:
            def __init__(self, recipient, recipient_name, subject_line, content):
                self.recipients = [recipient]
                self.to_name = recipient_name
                self.subject = subject_line
                self.html_content = content
                self.body = content  # Keep compatibility with existing .body checks in tests
        
        outbox.append(MockMessage(to_email, to_name, subject, html_content))
        return True

    api_key = current_app.config.get("BREVO_API_KEY")
    if not api_key:
        current_app.logger.warning("Brevo API key (BREVO_API_KEY) is not set; skipping email send")
        return False

    client = Brevo(api_key=api_key)
    sender_email = current_app.config.get("BREVO_SENDER_EMAIL", "support@reuni.ac.uk")
    
    try:
        client.transactional_emails.send_transac_email(
            sender=SendTransacEmailRequestSender(email=sender_email, name="Reuni"),
            to=[SendTransacEmailRequestToItem(email=to_email, name=to_name)],
            subject=subject,
            html_content=html_content,
        )
        return True
    except ApiError as e:
        current_app.logger.error(f"Brevo API error sending email to {to_email}: {e}")
        return False
    except Exception as e:
        current_app.logger.error(f"Unexpected error sending email to {to_email}: {e}")
        return False
