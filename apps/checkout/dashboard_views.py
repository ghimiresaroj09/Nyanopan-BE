"""Admin dashboard summary endpoint."""

from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Category, Product, ProductVariant
from apps.common.permissions import IsAdminUser
from apps.common.responses import SuccessEnvelopeMixin
from apps.accounts.models import User
from apps.cms.models import ContactMessage, Subscription

from .models import Order, OrderItem
from .serializers import OrderSerializer


@extend_schema(
    tags=["Admin - Dashboard"],
    description=(
        "Returns store KPIs, comparison with the preceding period, daily sales, "
        "order status counts, recent orders, top selling products, catalog "
        "counts, contact message counts, and newsletter subscribers. "
        "Optional `days` query parameter accepts 7, 30, or 90 (default 30)."
    ),
)
class AdminDashboardView(SuccessEnvelopeMixin, APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        try:
            days = int(request.query_params.get("days", 30))
        except (TypeError, ValueError):
            days = 30
        if days not in (7, 30, 90):
            days = 30

        today = timezone.localdate()
        start_date = today - timedelta(days=days - 1)
        previous_start = start_date - timedelta(days=days)
        start_at = timezone.make_aware(
            timezone.datetime.combine(start_date, timezone.datetime.min.time())
        )
        previous_start_at = timezone.make_aware(
            timezone.datetime.combine(previous_start, timezone.datetime.min.time())
        )
        today_start = timezone.make_aware(
            timezone.datetime.combine(today, timezone.datetime.min.time())
        )
        now = timezone.now()

        current_orders = Order.objects.filter(created_at__gte=start_at, created_at__lte=now)
        previous_orders = Order.objects.filter(
            created_at__gte=previous_start_at, created_at__lt=start_at
        )
        current_sales = current_orders.exclude(status=Order.Status.CANCELLED).aggregate(
            total=Sum("product_subtotal"), count=Count("id")
        )
        previous_sales = previous_orders.exclude(status=Order.Status.CANCELLED).aggregate(
            total=Sum("product_subtotal"), count=Count("id")
        )
        current_total = current_sales["total"] or 0
        previous_total = previous_sales["total"] or 0
        current_order_count = current_sales["count"] or 0
        previous_order_count = previous_sales["count"] or 0

        daily_sales = list(
            current_orders.exclude(status=Order.Status.CANCELLED)
            .annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(revenue=Sum("product_subtotal"), orders=Count("id"))
            .order_by("day")
        )
        sales_by_day = {row["day"]: row for row in daily_sales}
        sales_series = [
            {
                "date": (start_date + timedelta(days=i)).isoformat(),
                "revenue": sales_by_day.get(start_date + timedelta(days=i), {}).get("revenue") or 0,
                "orders": sales_by_day.get(start_date + timedelta(days=i), {}).get("orders", 0),
            }
            for i in range(days)
        ]

        statuses = {
            row["status"]: row["count"]
            for row in Order.objects.values("status").annotate(count=Count("id"))
        }
        top_products = list(
            OrderItem.objects.filter(
                order__created_at__gte=start_at,
                order__created_at__lte=now,
            )
            .exclude(order__status=Order.Status.CANCELLED)
            .values("product_name", "sku")
            .annotate(quantity_sold=Sum("quantity"), revenue=Sum("line_total"))
            .order_by("-quantity_sold", "product_name")[:5]
        )
        recent_orders = (
            Order.objects.select_related("delivery_location")
            .prefetch_related("items", "status_timeline__changed_by")
            .order_by("-created_at")[:10]
        )

        return Response({
            "period": {
                "days": days,
                "start_date": start_date.isoformat(),
                "end_date": today.isoformat(),
                "previous_start_date": previous_start.isoformat(),
                "previous_end_date": (start_date - timedelta(days=1)).isoformat(),
            },
            "sales": {
                "revenue": current_total,
                "previous_revenue": previous_total,
                "revenue_change_percent": _percent_change(current_total, previous_total),
                "orders": current_order_count,
                "previous_orders": previous_order_count,
                "orders_change_percent": _percent_change(current_order_count, previous_order_count),
                "average_order_value": round(current_total / current_order_count, 2) if current_order_count else 0,
                "currency": "NPR",
                "daily": sales_series,
            },
            "orders": {
                "total": Order.objects.count(),
                "by_status": {status: statuses.get(status, 0) for status, _ in Order.Status.choices},
                "today": Order.objects.filter(created_at__gte=today_start, created_at__lte=now).count(),
                "recent": OrderSerializer(recent_orders, many=True, context={"request": request}).data,
            },
            "top_products": top_products,
            "catalog": {
                "products": Product.objects.count(),
                "active_products": Product.objects.filter(is_active=True).count(),
                "categories": Category.objects.count(),
                "active_categories": Category.objects.filter(is_active=True).count(),
                "variants": ProductVariant.objects.count(),
                "active_variants": ProductVariant.objects.filter(is_active=True).count(),
            },
            "customers": {"total": User.objects.filter(is_staff=False).count()},
            "contact_messages": {
                "total": ContactMessage.objects.count(),
                "new": ContactMessage.objects.filter(status=ContactMessage.StatusChoices.NEW).count(),
                "unresolved": ContactMessage.objects.filter(
                    status__in=[ContactMessage.StatusChoices.NEW, ContactMessage.StatusChoices.IN_PROGRESS]
                ).count(),
            },
            "newsletter": {
                "total_subscribers": Subscription.objects.count(),
                "active_subscribers": Subscription.objects.filter(is_active=True).count(),
            },
        })


def _percent_change(current, previous):
    if not previous:
        return 100 if current else 0
    return round((current - previous) * 100 / previous, 2)
