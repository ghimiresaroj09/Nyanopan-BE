"""CMS URL Configuration - Public endpoints."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ContactUsPublicView,
    HomepageCollectionsPublicView,
    HomepagePublicView,
    OurMakersPublicView,
    OurStoryPublicView,
    OurSustainabilityPublicView,
    PolicyPublicViewSet,
    SiteConfigurationPublicView,
    SubscriptionPublicView,
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
    path("subscription/", SubscriptionPublicView.as_view(), name="subscription-public"),
    path("contact-us/", ContactUsPublicView.as_view(), name="contact-us-public"),
] + router.urls
