"""CMS URL Configuration - Public endpoints."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    HomepageCollectionsPublicView,
    HomepagePublicView,
    OurMakersPublicView,
    OurStoryPublicView,
    OurSustainabilityPublicView,
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
    path("our-sustainability/", OurSustainabilityPublicView.as_view(), name="our-sustainability-public"),
    path("homepage/", HomepagePublicView.as_view(), name="homepage-public"),
    path("homepage/collections/", HomepageCollectionsPublicView.as_view(), name="homepage-collections-public"),
] + router.urls
