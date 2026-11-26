from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.common.permissions import IsAdminUser
from apps.common.responses import SuccessEnvelopeMixin
from apps.common.pagination import paginate_list_or_return

from .models import DeliveryLocation, Order, OrderStatusEvent
from .emails import send_order_status_email
from .serializers import (
    AdminOrderDeliveryUpdateSerializer,
    AdminOrderStatusUpdateSerializer,
    DeliveryLocationAdminSerializer,
    OrderSerializer,
    OrderStatusEventSerializer,
)


@extend_schema(tags=["Admin - Orders"])
class AdminOrderViewSet(SuccessEnvelopeMixin, ReadOnlyModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = OrderSerializer
    lookup_value_converter = "uuid"

    def get_queryset(self):
        queryset = Order.objects.select_related("delivery_location").prefetch_related(
            "items", "status_timeline__changed_by"
        )
        status_value = self.request.query_params.get("status")
        if status_value:
            queryset = queryset.filter(status=status_value.upper())
        search = self.request.query_params.get("search")
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(customer_name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
                | Q(items__sku__icontains=search)
            ).distinct()
        return queryset.order_by("-created_at")

    @action(detail=True, methods=["patch"], url_path="delivery")
    @extend_schema(
        request=AdminOrderDeliveryUpdateSerializer,
        responses={200: OrderSerializer},
        description=(
            "Change the delivery location for an order. The delivery fee is taken from the "
            "location's current configuration (zero when it is free), saved as an order "
            "snapshot, and the order total is recalculated."
        ),
    )
    @transaction.atomic
    def update_delivery(self, request, pk=None):
        order = get_object_or_404(Order.objects.select_for_update(), pk=pk)
        serializer = AdminOrderDeliveryUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        location = get_object_or_404(
            DeliveryLocation.objects.select_for_update(),
            pk=serializer.validated_data["delivery_location_id"],
            is_active=True,
        )
        new_charge = Decimal("0.00") if location.is_free else location.delivery_charge
        previous_location_name = order.delivery_location_name or order.city_district
        order.delivery_location = location
        order.delivery_location_name = location.name
        order.city_district = location.name
        order.delivery_charge = new_charge
        order.subtotal = order.product_subtotal + new_charge
        order.save(update_fields=[
            "delivery_location", "delivery_location_name", "city_district",
            "delivery_charge", "subtotal", "updated_at",
        ])
        OrderStatusEvent.objects.create(
            order=order,
            from_status=order.status,
            to_status=order.status,
            note=(
                f"Delivery location changed from '{previous_location_name}' to "
                f"'{location.name}'. Delivery charge: {new_charge} {order.currency}."
            ),
            changed_by=request.user,
        )
        order = Order.objects.select_related("delivery_location").prefetch_related(
            "items", "status_timeline__changed_by"
        ).get(pk=order.pk)
        transaction.on_commit(
            lambda: send_order_status_email(
                order,
                old_status=order.get_status_display(),
                note=f"Delivery location updated to {location.name}; delivery charge is {new_charge} {order.currency}.",
            )
        )
        return Response(OrderSerializer(order).data)

    @action(detail=True, methods=["get"], url_path="timeline")
    @extend_schema(responses={200: OrderStatusEventSerializer(many=True)})
    @transaction.atomic
    def status_timeline(self, request, pk=None):
        order = get_object_or_404(Order.objects.select_for_update(), pk=pk)
        events = order.status_timeline.select_related("changed_by").all()
        return paginate_list_or_return(
            request,
            events,
            OrderStatusEventSerializer,
            {"request": request},
        )

    @action(detail=True, methods=["patch"], url_path="status")
    @extend_schema(request=AdminOrderStatusUpdateSerializer, responses={200: OrderSerializer})
    @transaction.atomic
    def update_status(self, request, pk=None):
        order = get_object_or_404(Order.objects.select_for_update(), pk=pk)
        serializer = AdminOrderStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]
        if new_status == order.status:
            raise ValidationError({"status": "The order already has this status."})
        previous_status = order.status
        order.status = new_status
        order.save(update_fields=["status", "updated_at"])
        note = serializer.validated_data["note"]
        OrderStatusEvent.objects.create(
            order=order,
            from_status=previous_status,
            to_status=new_status,
            note=note,
            changed_by=request.user,
        )
        order = Order.objects.prefetch_related("items", "status_timeline__changed_by").get(pk=order.pk)
        transaction.on_commit(
            lambda: send_order_status_email(order, old_status=previous_status, note=note)
        )
        return Response(OrderSerializer(order).data)


@extend_schema(tags=["Admin - Delivery Locations"])
class AdminDeliveryLocationViewSet(SuccessEnvelopeMixin, ModelViewSet):
    permission_classes = [IsAdminUser]
    serializer_class = DeliveryLocationAdminSerializer
    queryset = DeliveryLocation.objects.all()
    lookup_value_converter = "uuid"


