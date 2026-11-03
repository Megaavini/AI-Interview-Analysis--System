# -------------------------------
# mailer.py - send e-mail through SMTP (app password)
# -------------------------------
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

import config


def smtp_configured():
    return bool(config.SMTP_USER and config.SMTP_APP_PASSWORD and config.MAIL_FROM)


def send_mail(to_addr, subject, text_body, html_body=None):
    """Returns (ok: bool, message: str). Never raises."""
    if not smtp_configured():
        return False, 'SMTP is not configured (set SMTP_USER, SMTP_APP_PASSWORD, MAIL_FROM in .env)'
    if not to_addr:
        return False, 'Candidate has no e-mail address'

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = formataddr(('AI Interview System', config.MAIL_FROM))
    msg['To'] = to_addr
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype='html')

    try:
        if config.SMTP_PORT == 465:
            with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT, timeout=20,
                                  context=ssl.create_default_context()) as s:
                s.login(config.SMTP_USER, config.SMTP_APP_PASSWORD.replace(' ', ''))
                s.send_message(msg)
        else:
            with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20) as s:
                s.ehlo()
                s.starttls(context=ssl.create_default_context())
                s.ehlo()
                s.login(config.SMTP_USER, config.SMTP_APP_PASSWORD.replace(' ', ''))
                s.send_message(msg)
        return True, 'sent'
    except smtplib.SMTPAuthenticationError:
        return False, 'SMTP login failed - check the app password / username'
    except Exception as e:  # network, DNS, TLS ...
        return False, f'{type(e).__name__}: {e}'
