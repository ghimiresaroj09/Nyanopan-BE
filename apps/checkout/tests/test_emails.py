from decimal import Decimal

import pytest
from django.core import mail
from django.test import override_settings

from apps.checkout.emails import send_new_order_emails, send_order_status_email
from apps.checkout.models import Order
from apps.cms.models import SiteConfiguration


@pytest.fixture
def order(db):
    SiteConfiguration.objects.create(email="admin@example.com")
    return Order.objects.create(
        customer_name="Customer",
        email="customer@example.com",
        phone="123456789",
        address="Somewhere",
        subtotal=Decimal("10.00"),
        product_subtotal=Decimal("10.00"),
        currency="USD",
    )


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="shop@example.com",
)
@pytest.mark.django_db
def test_new_order_email_goes_to_customer_and_admin(order):
    send_new_order_emails(order)

    assert len(mail.outbox) == 2
    assert mail.outbox[0].to == ["customer@example.com"]
    assert mail.outbox[1].to == ["admin@example.com"]
    assert mail.outbox[1].subject.startswith("New order at Nyanopan")
    assert mail.outbox[0].alternatives[0][1] == "text/html"
    assert "Thank you" in mail.outbox[0].alternatives[0][0]
    assert "Time to prepare something special" in mail.outbox[1].alternatives[0][0]


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="shop@example.com",
)
@pytest.mark.django_db
def test_order_status_email_goes_only_to_customer(order):
    send_order_status_email(order, old_status="Pending")

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["customer@example.com"]
    assert "reviewing your order" in mail.outbox[0].subject
    assert mail.outbox[0].alternatives[0][1] == "text/html"
