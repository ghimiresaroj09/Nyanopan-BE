"""CMS URL Configuration - Admin endpoints."""

from django.urls import path

from .views import SiteConfigurationAdminView

app_name = "cms_admin"

urlpatterns = [
    path("configuration/", SiteConfigurationAdminView.as_view(), name="configuration-admin"),
]
