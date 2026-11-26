import logging
from email.mime.image import MIMEImage
from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from apps.cms.models import SiteConfiguration
from .models import Order

logger = logging.getLogger(__name__)


def _site_configuration():
    try:
        return SiteConfiguration.objects.filter(pk=1).first()
    except Exception:
        logger.exception("Unable to load site configuration for order email")
        return None


def _send_order_email(*, subject, message, recipients, html_template=None, context=None):
    recipients = sorted({email.strip() for email in recipients if email and email.strip()})
    if not recipients:
        logger.warning("Order email '%s' skipped because no recipient is configured", subject)
        return
    config = _site_configuration()
    sender = (
        config.email if config and config.email
        else getattr(settings, "DEFAULT_FROM_EMAIL", "")
    )
    if not sender:
        logger.warning("Order email '%s' skipped because DEFAULT_FROM_EMAIL is unset", subject)
        return
    try:
        email = EmailMultiAlternatives(subject, message, sender, recipients)
        if html_template:
            email.attach_alternative(
                render_to_string(html_template, context or {}), "text/html"
            )
            logo_path = (
                Path(__file__).resolve().parent
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
    except Exception:
        logger.exception("Failed to send order email '%s' to %s", subject, recipients)


def _order_message(order, *, heading, status_note=""):
    lines = [
        heading,
        f"Order: {order.pk}",
        f"Status: {order.get_status_display()}",
        f"Customer: {order.customer_name}",
        f"Email: {order.email}",
        f"Phone: {order.phone}",
    ]
    if order.alternate_phone:
        lines.append(f"Alternate phone: {order.alternate_phone}")
    if order.company_name:
        lines.append(f"Company: {order.company_name}")
    if order.pan_vat_number:
        lines.append(f"PAN/VAT: {order.pan_vat_number}")
    lines.extend([
        f"Delivery location: {order.delivery_location_name or order.city_district}",
        f"Address: {order.address}",
    ])
    if order.landmark:
        lines.append(f"Landmark: {order.landmark}")
    lines.extend(["", "Items:"])
    for item in order.items.all():
        label = item.product_name
        if item.variant_name:
            label += f" — {item.variant_name}"
        lines.append(
            f"- {label} (SKU {item.sku}) x {item.quantity}: "
            f"{item.line_total} {order.currency}"
        )
    lines.extend([
        "",
        f"Product subtotal: {order.product_subtotal} {order.currency}",
        f"Delivery charge: {order.delivery_charge} {order.currency}",
        f"Total: {order.subtotal} {order.currency}",
    ])
    if order.notes:
        lines.extend(["", f"Order note: {order.notes}"])
    if status_note:
        lines.extend(["", f"Update note: {status_note}"])
    config = _site_configuration()
    if config:
        if config.phone:
            lines.extend(["", f"Contact phone: {config.phone}"])
        if config.whatsapp:
            lines.append(f"WhatsApp: {config.whatsapp}")
        if config.address:
            lines.append(f"Business address: {config.address}")
    return "\n".join(lines)


def send_new_order_emails(order):
    config = _site_configuration()
    context = _email_context(order)
    customer_message = _order_message(
        order, heading="Thank you for choosing Nyanopan. We have received your order."
    )
    _send_order_email(
        subject=f"Order received — thank you for choosing Nyanopan! (#{order.pk})",
        message=customer_message,
        recipients=[order.email],
        html_template="checkout/emails/customer_order_received.html",
        context=context,
    )
    if config and config.email:
        _send_order_email(
            subject=f"New order at Nyanopan — {order.customer_name} (#{order.pk})",
            message=_order_message(order, heading="A new order has been placed."),
            recipients=[config.email],
            html_template="checkout/emails/admin_new_order.html",
            context=context,
        )
    else:
        logger.warning("New order notification skipped: site configuration email is empty")


def send_order_status_email(order, *, old_status, note=""):
    status_key = order.status
    status_copy = {
        Order.Status.PENDING: (
            "We’re getting your order ready for review. We’ll share another update "
            "as soon as our team confirms the next step."
        ),
        Order.Status.CONFIRMED: (
            "Your order is confirmed! Our team is preparing your Nyanopan pieces "
            "with care."
        ),
        Order.Status.PROCESSING: (
            "Your order is being prepared. We’ll let you know when it moves to "
            "the next stage."
        ),
        Order.Status.SHIPPED: (
            "Good news: your order is on its way. Please keep your phone nearby "
            "for delivery coordination."
        ),
        Order.Status.DELIVERED: (
            "Your order has been delivered. We hope you enjoy your Nyanopan "
            "purchase—thank you for supporting us."
        ),
        Order.Status.CANCELLED: (
            "Your order has been cancelled. If you think this was a mistake or "
            "need help, please contact our team."
        ),
    }
    message_copy = status_copy.get(
        status_key,
        f"Your order is now {order.get_status_display()}. We’ll keep you updated.",
    )
    context = _email_context(
        order,
        status_message=message_copy,
        old_status=old_status,
        status_note=note,
    )
    message = _order_message(
        order,
        heading=message_copy,
        status_note=note,
    )
    _send_order_email(
        subject=_status_subject(order),
        message=message,
        recipients=[order.email],
        html_template="checkout/emails/customer_order_status.html",
        context=context,
    )


def _status_subject(order):
    subject_copy = {
        Order.Status.PENDING: "We’re reviewing your order",
        Order.Status.CONFIRMED: "Your Nyanopan order is confirmed",
        Order.Status.PROCESSING: "Your order is being prepared with care",
        Order.Status.SHIPPED: "Your Nyanopan order is on its way",
        Order.Status.DELIVERED: "Your Nyanopan order has arrived",
        Order.Status.CANCELLED: "An update about your Nyanopan order",
    }
    label = subject_copy.get(order.status, f"Your order is {order.get_status_display()}")
    return f"{label} · #{order.pk}"


def _email_context(order, **extra):
    config = _site_configuration()
    context = {
        "order": order,
        "items": order.items.all(),
        "site": config,
        "status_label": order.get_status_display(),
        "currency": order.currency or "NPR",
    }
    context.update(extra)
    return context
