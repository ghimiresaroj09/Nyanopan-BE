"""CMS URL Configuration - Public endpoints."""

from django.urls import path

from .views import SiteConfigurationPublicView

app_name = "cms"

urlpatterns = [
    path("configuration/", SiteConfigurationPublicView.as_view(), name="configuration-public"),
]
