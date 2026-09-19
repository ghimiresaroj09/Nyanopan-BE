"""CMS URL Configuration - Admin endpoints."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CollectionAdminViewSet,
    HomepageAdminView,
    HomepageCollectionsAdminView,
    OurMakersAdminView,
    OurStoryAdminView,
    OurSustainabilityAdminView,
    PolicyAdminViewSet,
    SiteConfigurationAdminView,
    TeamMemberAdminViewSet,
)

app_name = "cms_admin"

router = DefaultRouter()
router.register(r'policies', PolicyAdminViewSet, basename='policy-admin')
router.register(r'team-members', TeamMemberAdminViewSet, basename='team-member-admin')
router.register(r'collections', CollectionAdminViewSet, basename='collection-admin')

urlpatterns = [
    path("configuration/", SiteConfigurationAdminView.as_view(), name="configuration-admin"),
    path("our-makers/", OurMakersAdminView.as_view(), name="our-makers-admin"),
    path("our-story/", OurStoryAdminView.as_view(), name="our-story-admin"),
    path("our-sustainability/", OurSustainabilityAdminView.as_view(), name="our-sustainability-admin"),
    path("homepage/", HomepageAdminView.as_view(), name="homepage-admin"),
    path("homepage/collections/", HomepageCollectionsAdminView.as_view(), name="homepage-collections-admin"),
] + router.urls
