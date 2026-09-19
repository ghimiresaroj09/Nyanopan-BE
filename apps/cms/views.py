"""CMS views for site configuration."""

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAdminUser

from apps.common.responses import SuccessEnvelopeMixin

from .models import SiteConfiguration
from .serializers import SiteConfigurationPublicSerializer, SiteConfigurationSerializer


@extend_schema(
    auth=[],
    tags=["Public - Site Configuration"],
    description="Get site configuration including contact information and social media links. No authentication required.",
)
class SiteConfigurationPublicView(SuccessEnvelopeMixin, RetrieveAPIView):
    """Public read-only endpoint for site configuration."""
    
    serializer_class = SiteConfigurationPublicSerializer
    success_message = "Site configuration retrieved successfully."
    permission_classes = []
    authentication_classes = []
    
    def get_object(self):
        return SiteConfiguration.get_config()


@extend_schema(
    tags=["Admin - Site Configuration"],
    description="Get and update site configuration. Admin access only.",
)
class SiteConfigurationAdminView(SuccessEnvelopeMixin, RetrieveUpdateAPIView):
    """Admin endpoint to view and update site configuration."""
    
    serializer_class = SiteConfigurationSerializer
    permission_classes = [IsAdminUser]
    
    def get_success_message(self, request=None):
        if request and request.method == 'PUT':
            return "Site configuration updated successfully."
        elif request and request.method == 'PATCH':
            return "Site configuration updated successfully."
        return "Site configuration retrieved successfully."
    
    def get_object(self):
        return SiteConfiguration.get_config()
