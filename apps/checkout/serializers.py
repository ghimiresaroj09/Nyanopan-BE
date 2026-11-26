from rest_framework import serializers

from .models import DeliveryLocation, Order, OrderItem, OrderStatusEvent


class CheckoutItemSerializer(serializers.Serializer):
    variantId = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=99)


class CheckoutInputSerializer(serializers.Serializer):
    items = CheckoutItemSerializer(many=True, allow_empty=False)
    customer_name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=40)
    alternate_phone = serializers.CharField(max_length=40, required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    company_name = serializers.CharField(max_length=200, required=False, allow_blank=True, default="")
    pan_vat_number = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    delivery_location_id = serializers.UUIDField()
    address = serializers.CharField()
    landmark = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class OrderItemSerializer(serializers.ModelSerializer):
    product_image = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["product_name", "product_image", "variant_name", "sku", "unit_price", "quantity", "line_total"]

    def get_product_image(self, item):
        """Return the catalog product's primary image for this purchased variant."""
        variant = getattr(item, "variant", None)
        product = getattr(variant, "product", None)
        if product is None:
            return None

        image = product.feature_image
        image_owner = product
        if not image or not image.name:
            # Match catalog primary-image behavior: use a product attribute
            # value image when the product itself has no featured image.
            image_owner = (
                product.attribute_values.filter(
                    is_active=True,
                    attribute__is_active=True,
                    attribute_value__is_active=True,
                )
                .exclude(feature_image="")
                .order_by("-attribute__requires_image", "id")
                .first()
            )
            if image_owner is None or not image_owner.feature_image.name:
                return None
            image = image_owner.feature_image

        url = image.url
        request = self.context.get("request") if self.context else None
        if url.startswith("/") and request is not None:
            url = request.build_absolute_uri(url)
        return {
            "url": url,
            "title": image_owner.feature_image_title or "",
            "caption": image_owner.feature_image_caption or "",
            "alt": image_owner.feature_image_alt or "",
        }


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_timeline = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ["id", "status", "customer_name", "email", "phone", "alternate_phone", "notes", "company_name", "pan_vat_number", "city_district", "delivery_location", "delivery_location_name", "product_subtotal", "delivery_charge", "subtotal", "address", "landmark", "currency", "items", "status_timeline", "created_at"]

    def get_status_timeline(self, order):
        return OrderStatusEventSerializer(order.status_timeline.all(), many=True).data


class DeliveryLocationSerializer(serializers.ModelSerializer):
    effective_charge = serializers.SerializerMethodField()

    class Meta:
        model = DeliveryLocation
        fields = ["id", "name", "delivery_charge", "is_free", "effective_charge"]

    def get_effective_charge(self, location):
        from decimal import Decimal
        return Decimal("0.00") if location.is_free else location.delivery_charge


class DeliveryLocationAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeliveryLocation
        fields = ["id", "name", "delivery_charge", "is_free", "is_active", "created_at", "updated_at"]

class OrderStatusEventSerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()

    class Meta:
        model = OrderStatusEvent
        fields = ["id", "from_status", "to_status", "note", "changed_by_name", "created_at"]

    def get_changed_by_name(self, event):
        return event.changed_by.get_full_name() if event.changed_by else None


class AdminOrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.Status.choices)
    note = serializers.CharField(required=False, allow_blank=True, default="")


class AdminOrderDeliveryUpdateSerializer(serializers.Serializer):
    delivery_location_id = serializers.UUIDField()
