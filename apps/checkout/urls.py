from django.urls import path
from rest_framework.routers import DefaultRouter

from .admin_views import AdminDeliveryLocationViewSet, AdminOrderViewSet
from .views import CheckoutView, DeliveryLocationListView

admin_router = DefaultRouter()
admin_router.register("orders", AdminOrderViewSet, basename="admin-order")
admin_router.register("delivery-locations", AdminDeliveryLocationViewSet, basename="admin-delivery-location")

urlpatterns = [
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("delivery-locations/", DeliveryLocationListView.as_view(), name="delivery-location-list"),
]

admin_urlpatterns = admin_router.urls
