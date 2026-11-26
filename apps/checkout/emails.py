import logging

from django.conf import settings
from django.core.mail import send_mail

from apps.cms.models import SiteConfiguration

logger = logging.getLogger(__name__)


def _site_configuration():
    try:
        return SiteConfiguration.objects.filter(pk=1).first()
    except Exception:
        logger.exception("Unable to load site configuration for order email")
        return None


def _send_order_email(*, subject, message, recipients):
    recipients = sorted({email.strip() for email in recipients if email and email.strip()})
    if not recipients:
        logger.warning("Order email '%s' skipped because no recipient is configured", subject)
        return
    sender = getattr(settings, "DEFAULT_FROM_EMAIL", "")
    if not sender:
        config = _site_configuration()
        sender = config.email if config and config.email else None
    if not sender:
        logger.warning("Order email '%s' skipped because DEFAULT_FROM_EMAIL is unset", subject)
        return
    try:
        send_mail(subject, message, sender, recipients, fail_silently=False)
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
    customer_message = _order_message(order, heading="We received your order.")
    _send_order_email(
        subject=f"Order received: {order.pk}",
        message=customer_message,
        recipients=[order.email],
    )
    if config and config.email:
        _send_order_email(
            subject=f"New order placed: {order.pk}",
            message=_order_message(order, heading="A new order has been placed."),
            recipients=[config.email],
        )
    else:
        logger.warning("New order notification skipped: site configuration email is empty")


def send_order_status_email(order, *, old_status, note=""):
    config = _site_configuration()
    message = _order_message(
        order,
        heading=f"Your order status changed from {old_status} to {order.get_status_display()}.",
        status_note=note,
    )
    _send_order_email(
        subject=f"Order {order.pk} status: {order.get_status_display()}",
        message=message,
        recipients=[order.email],
    )
    if config and config.email:
        _send_order_email(
            subject=f"Order status updated: {order.pk}",
            message=message,
            recipients=[config.email],
        )
