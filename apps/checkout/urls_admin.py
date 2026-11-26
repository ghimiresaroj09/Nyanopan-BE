from django.urls import path

from .dashboard_views import AdminDashboardView
from .urls import admin_urlpatterns

urlpatterns = [
    path("dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    *admin_urlpatterns,
]
