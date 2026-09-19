"""CMS views for site configuration and policies."""

from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.common.responses import SuccessEnvelopeMixin

from .models import (
    OurMakers,
    OurStory,
    OurSustainability,
    Policy,
    SiteConfiguration,
    TeamMember,
)
from .serializers import (
    OurMakersPublicSerializer,
    OurMakersSerializer,
    OurStoryPublicSerializer,
    OurStorySerializer,
    OurSustainabilityPublicSerializer,
    OurSustainabilitySerializer,
    PolicyPublicSerializer,
    PolicySerializer,
    SiteConfigurationPublicSerializer,
    SiteConfigurationSerializer,
    TeamMemberSerializer,
)


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



@extend_schema(
    auth=[],
    tags=["Public - Policies"],
    description=(
        "List and retrieve policy documents by type.\n\n"
        "**Available policy types:**\n"
        "- `SHIPPING` - Shipping Policy\n"
        "- `EXCHANGES_RETURNS` - Exchanges & Returns Policy\n"
        "- `PRIVACY_POLICY` - Privacy Policy\n"
        "- `TERMS_CONDITIONS` - Terms and Conditions\n\n"
        "**Filtering:**\n"
        "Use `?type=SHIPPING` to filter by specific policy type.\n\n"
        "**Examples:**\n"
        "- List all policies: `GET /api/v1/policies/`\n"
        "- Get shipping policy: `GET /api/v1/policies/{id}/`\n"
        "- Filter by type: `GET /api/v1/policies/?type=PRIVACY_POLICY`"
    ),
    parameters=[
        OpenApiParameter(
            name='type',
            description='Filter by policy type',
            required=False,
            type=str,
            enum=['SHIPPING', 'EXCHANGES_RETURNS', 'PRIVACY_POLICY', 'TERMS_CONDITIONS']
        ),
    ],
)
class PolicyPublicViewSet(SuccessEnvelopeMixin, ReadOnlyModelViewSet):
    """Public read-only endpoint for policies."""
    
    serializer_class = PolicyPublicSerializer
    success_message = "Policies retrieved successfully."
    permission_classes = []
    authentication_classes = []
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type']
    
    def get_queryset(self):
        return Policy.objects.filter(is_active=True).order_by('type')


@extend_schema(
    tags=["Admin - Policies"],
    description="Manage policy documents. Admin access only.",
)
class PolicyAdminViewSet(SuccessEnvelopeMixin, ModelViewSet):
    """Admin endpoint to manage policies."""
    
    serializer_class = PolicySerializer
    permission_classes = [IsAdminUser]
    queryset = Policy.objects.all().order_by('type')
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['type', 'is_active']
    
    def get_success_message(self, request=None):
        if request and request.method == 'POST':
            return "Policy created successfully."
        elif request and request.method in ['PUT', 'PATCH']:
            return "Policy updated successfully."
        elif request and request.method == 'DELETE':
            return "Policy deleted successfully."
        return "Policy retrieved successfully."



@extend_schema(
    auth=[],
    tags=["Public - Our Makers"],
    description="Get Our Makers/Team page with team member information. No authentication required.",
)
class OurMakersPublicView(SuccessEnvelopeMixin, RetrieveAPIView):
    """Public read-only endpoint for Our Makers page."""
    
    serializer_class = OurMakersPublicSerializer
    success_message = "Our Makers page retrieved successfully."
    permission_classes = []
    authentication_classes = []
    
    def get_object(self):
        return OurMakers.get_page()


@extend_schema(
    tags=["Admin - Our Makers"],
    description="Manage Our Makers page and team members. Admin access only.",
)
class OurMakersAdminView(SuccessEnvelopeMixin, RetrieveUpdateAPIView):
    """Admin endpoint to view and update Our Makers page."""
    
    serializer_class = OurMakersSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_success_message(self, request=None):
        if request and request.method in ['PUT', 'PATCH']:
            return "Our Makers page updated successfully."
        return "Our Makers page retrieved successfully."
    
    def get_object(self):
        return OurMakers.get_page()


@extend_schema(
    tags=["Admin - Team Members"],
    description="Manage team members. Admin access only.",
)
class TeamMemberAdminViewSet(SuccessEnvelopeMixin, ModelViewSet):
    """Admin endpoint to manage team members."""
    
    serializer_class = TeamMemberSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    queryset = TeamMember.objects.all().order_by('sort_order', 'name')
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'our_makers']
    
    def get_success_message(self, request=None):
        if request and request.method == 'POST':
            return "Team member created successfully."
        elif request and request.method in ['PUT', 'PATCH']:
            return "Team member updated successfully."
        elif request and request.method == 'DELETE':
            return "Team member deleted successfully."
        return "Team member retrieved successfully."



@extend_schema(
    auth=[],
    tags=["Public - Our Story"],
    description="Get Our Story page with multiple sections and subsections. No authentication required.",
)
class OurStoryPublicView(SuccessEnvelopeMixin, RetrieveAPIView):
    """Public read-only endpoint for Our Story page."""
    
    serializer_class = OurStoryPublicSerializer
    success_message = "Our Story page retrieved successfully."
    permission_classes = []
    authentication_classes = []
    
    def get_object(self):
        return OurStory.get_page()


@extend_schema(
    tags=["Admin - Our Story"],
    description="Manage Our Story page. Admin access only.",
)
class OurStoryAdminView(SuccessEnvelopeMixin, RetrieveUpdateAPIView):
    """Admin endpoint to view and update Our Story page."""
    
    serializer_class = OurStorySerializer
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_success_message(self, request=None):
        if request and request.method in ['PUT', 'PATCH']:
            return "Our Story page updated successfully."
        return "Our Story page retrieved successfully."
    
    def get_object(self):
        return OurStory.get_page()


@extend_schema(
    auth=[],
    tags=["Public - Our Sustainability"],
    description="Get Our Sustainability page with sections. No authentication required.",
)
class OurSustainabilityPublicView(SuccessEnvelopeMixin, RetrieveAPIView):
    """Public read-only endpoint for Our Sustainability page."""
    
    serializer_class = OurSustainabilityPublicSerializer
    success_message = "Our Sustainability page retrieved successfully."
    permission_classes = []
    authentication_classes = []
    
    def get_object(self):
        return OurSustainability.get_page()


@extend_schema(
    tags=["Admin - Our Sustainability"],
    description="Manage Our Sustainability page. Admin access only.",
)
class OurSustainabilityAdminView(SuccessEnvelopeMixin, RetrieveUpdateAPIView):
    """Admin endpoint to view and update Our Sustainability page."""
    
    serializer_class = OurSustainabilitySerializer
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_success_message(self, request=None):
        if request and request.method in ['PUT', 'PATCH']:
            return "Our Sustainability page updated successfully."
        return "Our Sustainability page retrieved successfully."
    
    def get_object(self):
        return OurSustainability.get_page()



# ============================================================================
# HOMEPAGE VIEWS
# ============================================================================

from .models import Homepage, HomepageCollections, Collection
from .serializers import (
    HomepageSerializer,
    HomepagePublicSerializer,
    HomepageCollectionsSerializer,
    HomepageCollectionsPublicSerializer,
    CollectionSerializer,
)


@extend_schema(
    auth=[],
    tags=["Public - Homepage"],
    description="Get homepage content. No authentication required.",
)
class HomepagePublicView(SuccessEnvelopeMixin, RetrieveAPIView):
    """Public read-only endpoint for Homepage content."""
    
    serializer_class = HomepagePublicSerializer
    success_message = "Homepage content retrieved successfully."
    permission_classes = []
    authentication_classes = []
    
    def get_object(self):
        return Homepage.get_homepage()


@extend_schema(
    tags=["Admin - Homepage"],
    description="Manage homepage content. Admin access only.",
)
class HomepageAdminView(SuccessEnvelopeMixin, RetrieveUpdateAPIView):
    """Admin endpoint to view and update Homepage content."""
    
    serializer_class = HomepageSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_success_message(self, request=None):
        if request and request.method in ['PUT', 'PATCH']:
            return "Homepage content updated successfully."
        return "Homepage content retrieved successfully."
    
    def get_object(self):
        return Homepage.get_homepage()


@extend_schema(
    auth=[],
    tags=["Public - Homepage Collections"],
    description="Get homepage collections. No authentication required.",
)
class HomepageCollectionsPublicView(SuccessEnvelopeMixin, RetrieveAPIView):
    """Public read-only endpoint for Homepage Collections."""
    
    serializer_class = HomepageCollectionsPublicSerializer
    success_message = "Homepage collections retrieved successfully."
    permission_classes = []
    authentication_classes = []
    
    def get_object(self):
        return HomepageCollections.get_collections_page()


@extend_schema(
    tags=["Admin - Homepage Collections"],
    description="Manage homepage collections. Admin access only.",
)
class HomepageCollectionsAdminView(SuccessEnvelopeMixin, RetrieveUpdateAPIView):
    """Admin endpoint to view and update Homepage Collections."""
    
    serializer_class = HomepageCollectionsSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    
    def get_success_message(self, request=None):
        if request and request.method in ['PUT', 'PATCH']:
            return "Homepage collections updated successfully."
        return "Homepage collections retrieved successfully."
    
    def get_object(self):
        return HomepageCollections.get_collections_page()


@extend_schema(
    tags=["Admin - Collections"],
    description="Manage individual collection items. Admin access only.",
)
class CollectionAdminViewSet(SuccessEnvelopeMixin, ModelViewSet):
    """Admin endpoint to manage collection items."""
    
    serializer_class = CollectionSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    queryset = Collection.objects.all().order_by('sort_order', 'name')
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active', 'homepage_collections']
    
    def get_success_message(self, request=None):
        if request and request.method == 'POST':
            return "Collection created successfully."
        elif request and request.method in ['PUT', 'PATCH']:
            return "Collection updated successfully."
        elif request and request.method == 'DELETE':
            return "Collection deleted successfully."
        return "Collection retrieved successfully."
    
    def perform_create(self, serializer):
        # Auto-assign to singleton homepage collections if not provided
        if 'homepage_collections' not in serializer.validated_data:
            serializer.save(homepage_collections=HomepageCollections.get_collections_page())
        else:
            serializer.save()
