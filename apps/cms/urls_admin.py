"""CMS URL Configuration - Admin endpoints."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    OurMakersAdminView,
    OurStoryAdminView,
    PolicyAdminViewSet,
    SiteConfigurationAdminView,
    StorySubsectionAdminViewSet,
    TeamMemberAdminViewSet,
)

app_name = "cms_admin"

router = DefaultRouter()
router.register(r'policies', PolicyAdminViewSet, basename='policy-admin')
router.register(r'team-members', TeamMemberAdminViewSet, basename='team-member-admin')
router.register(r'story-subsections', StorySubsectionAdminViewSet, basename='story-subsection-admin')

urlpatterns = [
    path("configuration/", SiteConfigurationAdminView.as_view(), name="configuration-admin"),
    path("our-makers/", OurMakersAdminView.as_view(), name="our-makers-admin"),
    path("our-story/", OurStoryAdminView.as_view(), name="our-story-admin"),
] + router.urls

