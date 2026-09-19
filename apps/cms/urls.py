"""CMS URL Configuration - Public endpoints."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    OurMakersPublicView,
    OurStoryPublicView,
    PolicyPublicViewSet,
    SiteConfigurationPublicView,
)

app_name = "cms"

router = DefaultRouter()
router.register(r'policies', PolicyPublicViewSet, basename='policy')

urlpatterns = [
    path("configuration/", SiteConfigurationPublicView.as_view(), name="configuration-public"),
    path("our-makers/", OurMakersPublicView.as_view(), name="our-makers-public"),
    path("our-story/", OurStoryPublicView.as_view(), name="our-story-public"),
] + router.urls

