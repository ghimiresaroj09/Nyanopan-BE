from decimal import Decimal

from django.conf import settings
from django.db import transaction
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import ProductVariant
from apps.common.responses import SuccessEnvelopeMixin
from apps.common.pagination import paginate_list_or_return

from .emails import send_new_order_emails
from .models import DeliveryLocation, Order, OrderItem, OrderStatusEvent
from .serializers import CheckoutInputSerializer, DeliveryLocationSerializer, OrderSerializer


@extend_schema(
    tags=["Public - Checkout"],
    summary="Submit checkout",
    description=(
        "Submits customer details and frontend local-cart items to create a pending order. "
        "Each item requires `variantId` and `quantity`. Other local-storage fields such as "
        "name, image, option selections, and unitPrice are ignored. Active variants and their "
            "current prices are verified server-side. Select a delivery location using its ID "
            "from `GET /api/v1/delivery-locations/`; its configured delivery charge is added "
            "to the item subtotal."
    ),
    request=CheckoutInputSerializer,
    responses={201: OrderSerializer},
    examples=[OpenApiExample(
        "Checkout form submission",
        request_only=True,
        value={
            "items": [{"variantId": "0fd710ad-c604-4df3-97f9-d9bf70171ba1", "quantity": 1}],
            "customer_name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "+977 9800000000",
            "alternate_phone": "",
            "notes": "Please call before delivery.",
            "company_name": "",
            "pan_vat_number": "",
            "delivery_location_id": "00000000-0000-0000-0000-000000000001",
            "address": "Thamel, Kathmandu",
            "landmark": "Near the main square",
        },
    )],
)
class CheckoutView(SuccessEnvelopeMixin, APIView):
    permission_classes = [AllowAny]
    serializer_class = CheckoutInputSerializer
    success_message = "Checkout submitted successfully."

    @transaction.atomic
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        variant_ids = [item["variantId"] for item in data["items"]]
        if len(variant_ids) != len(set(variant_ids)):
            raise ValidationError({"items": "Each variant may appear once; combine duplicate quantities."})
        variants = {
            variant.id: variant
            for variant in ProductVariant.objects.select_related("product").select_for_update().filter(
                id__in=variant_ids, is_active=True, product__is_active=True
            )
        }
        unavailable = [str(variant_id) for variant_id in variant_ids if variant_id not in variants]
        if unavailable:
            raise ValidationError({"items": "Some variants are unavailable.", "variant_ids": unavailable})

        try:
            location = DeliveryLocation.objects.select_for_update().get(
                id=data["delivery_location_id"], is_active=True
            )
        except DeliveryLocation.DoesNotExist:
            raise ValidationError({"delivery_location_id": "Select an active delivery location."})
        delivery_charge = Decimal("0.00") if location.is_free else location.delivery_charge

        subtotal = sum(
            (variants[item["variantId"]].price * item["quantity"] for item in data["items"]),
            Decimal("0.00"),
        )
        order = Order.objects.create(
            customer_name=data["customer_name"], email=data["email"], phone=data["phone"],
            alternate_phone=data["alternate_phone"], notes=data["notes"],
            company_name=data["company_name"], pan_vat_number=data["pan_vat_number"],
            delivery_location=location, delivery_location_name=location.name,
            city_district=location.name,
            address=data["address"], landmark=data["landmark"],
            currency=getattr(settings, "STORE_CURRENCY", ""),
            product_subtotal=subtotal, delivery_charge=delivery_charge,
            subtotal=subtotal + delivery_charge,
        )
        OrderStatusEvent.objects.create(
            order=order, from_status="", to_status=order.status,
            note="Order created from checkout.",
        )
        OrderItem.objects.bulk_create([
            OrderItem(
                order=order,
                variant=variants[item["variantId"]],
                product_name=variants[item["variantId"]].product.name,
                variant_name=variants[item["variantId"]].name,
                sku=variants[item["variantId"]].sku,
                unit_price=variants[item["variantId"]].price,
                quantity=item["quantity"],
                line_total=variants[item["variantId"]].price * item["quantity"],
            )
            for item in data["items"]
        ])
        order = Order.objects.prefetch_related("items", "status_timeline").get(pk=order.pk)
        transaction.on_commit(lambda: send_new_order_emails(order))
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=["Public - Delivery"],
    summary="List delivery locations",
    description=(
        "Returns active locations for the checkout city/district selector. `effective_charge` "
        "is zero when `is_free` is true; otherwise it equals `delivery_charge`. Submit the "
        "selected location's `id` as `delivery_location_id` to checkout."
    ),
    responses={200: DeliveryLocationSerializer(many=True)},
)
class DeliveryLocationListView(SuccessEnvelopeMixin, APIView):
    permission_classes = [AllowAny]
    serializer_class = DeliveryLocationSerializer

    def get(self, request):
        locations = DeliveryLocation.objects.filter(is_active=True)
        return paginate_list_or_return(
            request, locations, DeliveryLocationSerializer, {"request": request}
        )
