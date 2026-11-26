"""Email notifications for contact form messages."""

import logging
from email.mime.image import MIMEImage
from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from apps.cms.models import SiteConfiguration

logger = logging.getLogger(__name__)


def _site_configuration():
    try:
        return SiteConfiguration.objects.filter(pk=1).first()
    except Exception:
        logger.exception("Unable to load site configuration for contact email")
        return None


def _send_contact_email(*, subject, text_body, recipients, template, context, reply_to=None):
    recipients = [address.strip() for address in recipients if address and address.strip()]
    if not recipients:
        logger.warning("Contact email '%s' skipped because no recipient is configured", subject)
        return False

    config = _site_configuration()
    sender = (config.email if config and config.email else settings.DEFAULT_FROM_EMAIL).strip()
    if not sender:
        logger.warning("Contact email '%s' skipped because no sender is configured", subject)
        return False

    try:
        email = EmailMultiAlternatives(
            subject,
            text_body,
            sender,
            recipients,
            reply_to=[reply_to] if reply_to else None,
        )
        email.attach_alternative(render_to_string(template, context), "text/html")
        logo_path = (
            Path(__file__).resolve().parents[1]
            / "checkout"
            / "templates"
            / "checkout"
            / "emails"
            / "assets"
            / "nyanopan-logo.png"
        )
        if logo_path.is_file():
            logo = MIMEImage(logo_path.read_bytes(), _subtype="png")
            logo.add_header("Content-ID", "<nyanopan-logo>")
            logo.add_header("Content-Disposition", "inline", filename="nyanopan-logo.png")
            email.attach(logo)
        email.send(fail_silently=False)
        return True
    except Exception:
        logger.exception("Failed to send contact email '%s' to %s", subject, recipients)
        return False


def send_contact_admin_notification(contact_message):
    """Notify the configured site contact when a visitor submits the form."""
    config = _site_configuration()
    if not config or not config.email:
        logger.warning("New contact notification skipped: site configuration email is empty")
        return False

    safe_subject = " ".join(contact_message.subject.splitlines()).strip()
    subject = f"New Nyanopan inquiry: {safe_subject} — {contact_message.name}"
    text_body = (
        f"New contact form message from {contact_message.name}.\n\n"
        f"Subject: {contact_message.subject}\n"
        f"Email: {contact_message.email}\n"
        f"Phone: {contact_message.phone or 'Not provided'}\n\n"
        f"{contact_message.message}"
    )
    return _send_contact_email(
        subject=subject,
        text_body=text_body,
        recipients=[config.email],
        reply_to=contact_message.email,
        template="cms/emails/admin_contact_message.html",
        context={"contact": contact_message},
    )


def send_contact_reply(contact_message, reply):
    """Email an admin's reply to the visitor who submitted the form."""
    config = _site_configuration()
    sender = config.email if config and config.email else settings.DEFAULT_FROM_EMAIL
    if not sender:
        logger.warning("Reply to contact message %s skipped: no sender is configured", contact_message.pk)
        return False

    original_subject = " ".join(contact_message.subject.splitlines()).strip()
    subject = (
        original_subject
        if original_subject.lower().startswith("re:")
        else f"Re: {original_subject}"
    )
    text_body = (
        f"Hi {contact_message.name},\n\n{reply}\n\n"
        "Warm regards,\nNyanopan"
    )
    return _send_contact_email(
        subject=subject,
        text_body=text_body,
        recipients=[contact_message.email],
        reply_to=sender,
        template="cms/emails/contact_message_reply.html",
        context={"contact": contact_message, "reply": reply},
    )
