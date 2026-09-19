"""CMS URL Configuration - Public endpoints."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PolicyPublicViewSet, SiteConfigurationPublicView

app_name = "cms"

router = DefaultRouter()
router.register(r'policies', PolicyPublicViewSet, basename='policy')

urlpatterns = [
    path("configuration/", SiteConfigurationPublicView.as_view(), name="configuration-public"),
] + router.urls

