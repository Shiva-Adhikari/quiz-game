# Standard library imports
import ssl
import smtplib
from email.message import EmailMessage

# Local imports
from src.core.config import settings


def send_email(email_receiver: str, otp: int) -> bool:
    html_content = f'get {otp}'
    em = EmailMessage()
    em['From'] = settings.SENDER_EMAIL
    em['To'] = email_receiver
    em['Subject'] = 'Verify Email'
    em.set_content(html_content, subtype='html')

    # establish tls/ssl connection
    context = ssl.create_default_context()

    try:
        # with help to properly close connection
        with smtplib.SMTP_SSL(
                settings.EMAIL_HOST.get_secret_value(),
                settings.EMAIL_PORT, context=context) as smtp:
            smtp.login(
                settings.SENDER_EMAIL,
                settings.SENDER_PASSWORD.get_secret_value())
            smtp.sendmail(
                settings.SENDER_EMAIL, email_receiver, em.as_string())
        return True
    except smtplib.SMTPRecipientsRefused:
        return False    # Email not Valid
    except Exception:
        return False    # Exception occured
