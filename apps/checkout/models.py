import uuid

from django.db import models

from apps.common.models import TimeStampedModel


class Order(TimeStampedModel):
    """Order snapshot created when a shopper submits checkout details."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        PROCESSING = "PROCESSING", "Processing"
        SHIPPED = "SHIPPED", "Shipped"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    customer_name = models.CharField(max_length=200)
    email = models.EmailField(blank=True, default="")
    phone = models.CharField(max_length=40)
    alternate_phone = models.CharField(max_length=40, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    company_name = models.CharField(max_length=200, blank=True, default="")
    pan_vat_number = models.CharField(max_length=100, blank=True, default="")
    city_district = models.CharField(max_length=150, blank=True, default="")
    delivery_location = models.ForeignKey(
        "checkout.DeliveryLocation", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="orders",
    )
    delivery_location_name = models.CharField(max_length=150, blank=True, default="")
    delivery_charge = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    product_subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    address = models.TextField(blank=True, default="")
    landmark = models.CharField(max_length=255, blank=True, default="")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    currency = models.CharField(max_length=3, blank=True, default="")
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)


class DeliveryLocation(TimeStampedModel):
    name = models.CharField(max_length=150, unique=True)
    delivery_charge = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_free = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("catalog.ProductVariant", null=True, blank=True, on_delete=models.SET_NULL, related_name="order_items")
    product_name = models.CharField(max_length=200)
    variant_name = models.CharField(max_length=200, blank=True, default="")
    sku = models.CharField(max_length=100)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    quantity = models.PositiveIntegerField()
    line_total = models.DecimalField(max_digits=14, decimal_places=2)


class OrderStatusEvent(models.Model):
    """Append-only audit entry for order creation and status transitions."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_timeline")
    from_status = models.CharField(max_length=20, blank=True, default="")
    to_status = models.CharField(max_length=20, choices=Order.Status.choices)
    note = models.TextField(blank=True, default="")
    changed_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="order_status_events",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["created_at", "id"]
