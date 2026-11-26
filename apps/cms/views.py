"""CMS views for site configuration and policies."""

from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, F, Q
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.filters import OrderingFilter
from rest_framework.generics import GenericAPIView, RetrieveAPIView, RetrieveUpdateAPIView, CreateAPIView, ListAPIView
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.common.responses import SuccessEnvelopeMixin

from .models import (
    OurMakers,
    OurStory,
    OurSustainability,
    FAQ,
    FAQCategory,
    Blog,
    BlogCategory,
    Policy,
    SiteConfiguration,
    TeamMember,
)
from .emails import send_contact_admin_notification, send_contact_reply
from .serializers import (
    OurMakersPublicSerializer,
    OurMakersSerializer,
    OurStoryPublicSerializer,
    OurStorySerializer,
    OurSustainabilityPublicSerializer,
    OurSustainabilitySerializer,
    PolicyPublicSerializer,
    PolicySerializer,
    FAQSerializer,
    FAQPublicSerializer,
    FAQCategorySerializer,
    FAQCategoryPublicSerializer,
    BlogSerializer,
    BlogPublicSerializer,
    BlogCategorySerializer,
    BlogCategoryPublicSerializer,
    SiteConfigurationPublicSerializer,
    SiteConfigurationSerializer,
    TeamMemberSerializer,
)
from .filters import BlogFilter


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



# ============================================================================
# SUBSCRIPTION VIEWS
# ============================================================================

from rest_framework.generics import CreateAPIView, ListAPIView

from .models import Subscription
from .serializers import SubscriptionCreateSerializer, SubscriptionSerializer


@extend_schema(
    auth=[],
    tags=["Public - Subscription"],
    description="Subscribe to newsletter. No authentication required.",
    request=SubscriptionCreateSerializer,
    responses={201: SubscriptionSerializer},
)
class SubscriptionPublicView(SuccessEnvelopeMixin, CreateAPIView):
    """Public endpoint to subscribe to newsletter."""
    
    serializer_class = SubscriptionCreateSerializer
    permission_classes = []
    authentication_classes = []
    
    def get_success_message(self, request=None):
        return "Successfully subscribed to newsletter."
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        
        # Return full subscription data
        response_serializer = SubscriptionSerializer(instance)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )


@extend_schema(
    tags=["Admin - Subscriptions"],
    description="List all newsletter subscriptions. Admin access only.",
)
class SubscriptionAdminListView(SuccessEnvelopeMixin, ListAPIView):
    """Admin endpoint to list all subscriptions."""
    
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAdminUser]
    queryset = Subscription.objects.all().order_by('-subscribed_at')
    success_message = "Subscriptions retrieved successfully."
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']



# ============================================================================
# CONTACT US VIEWS
# ============================================================================

from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView

from .models import ContactMessage, ContactMessageReply
from .serializers import (
    ContactMessageCreateSerializer,
    ContactMessageDetailSerializer,
    ContactMessageSerializer,
    ContactMessageReplyHistorySerializer,
    ContactMessageReplySerializer,
    ContactMessageUpdateSerializer,
)


@extend_schema(
    auth=[],
    tags=["Public - Contact Us"],
    description="Submit contact form message. No authentication required.",
    request=ContactMessageCreateSerializer,
    responses={201: ContactMessageSerializer},
)
class ContactUsPublicView(SuccessEnvelopeMixin, CreateAPIView):
    """Public endpoint to submit contact form."""
    
    serializer_class = ContactMessageCreateSerializer
    permission_classes = []
    authentication_classes = []
    
    def get_success_message(self, request=None):
        return "Thank you for contacting us. We'll get back to you soon."
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        send_contact_admin_notification(instance)
        
        # Return full message data
        response_serializer = ContactMessageSerializer(instance)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )


@extend_schema(
    tags=["Admin - Contact Messages"],
    description="List all contact messages. Admin access only.",
)
class ContactMessageAdminListView(SuccessEnvelopeMixin, ListAPIView):
    """Admin endpoint to list all contact messages."""
    
    serializer_class = ContactMessageSerializer
    permission_classes = [IsAdminUser]
    queryset = ContactMessage.objects.all().order_by('-created_at')
    success_message = "Contact messages retrieved successfully."
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']


@extend_schema(
    tags=["Admin - Contact Messages"],
    description="View and update contact message status. Admin access only.",
)
class ContactMessageAdminDetailView(SuccessEnvelopeMixin, RetrieveUpdateAPIView):
    """Admin endpoint to view and update contact message."""
    
    permission_classes = [IsAdminUser]
    queryset = ContactMessage.objects.prefetch_related("replies__sent_by")
    
    def get_success_message(self, request=None):
        if request and request.method in ['PUT', 'PATCH']:
            return "Contact message updated successfully."
        return "Contact message retrieved successfully."
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ContactMessageUpdateSerializer
        if self.request.method == 'GET':
            return ContactMessageDetailSerializer
        return ContactMessageSerializer


@extend_schema(
    tags=["Admin - Contact Messages"],
    description=(
        "Send a reply to the email address submitted with this contact message. "
        "Admin access only."
    ),
    request=ContactMessageReplySerializer,
)
class ContactMessageAdminReplyView(SuccessEnvelopeMixin, GenericAPIView):
    """Email an admin's reply to the contact message sender."""

    permission_classes = [IsAdminUser]
    serializer_class = ContactMessageReplySerializer

    def post(self, request, pk):
        from django.shortcuts import get_object_or_404

        message = get_object_or_404(ContactMessage, pk=pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reply_text = serializer.validated_data["reply"]
        if not send_contact_reply(message, reply_text):
            error = APIException(
                "Unable to send the reply email. Check the email configuration and try again.",
                code="contact_reply_delivery_failed",
            )
            error.status_code = status.HTTP_502_BAD_GATEWAY
            raise error

        original_subject = " ".join(message.subject.splitlines()).strip()
        subject = (
            original_subject
            if original_subject.lower().startswith("re:")
            else f"Re: {original_subject}"
        )
        ContactMessageReply.objects.create(
            contact_message=message,
            reply=reply_text,
            subject=subject,
            sent_by=request.user,
        )
        return Response(
            {"id": message.pk, "email": message.email, "subject": subject},
            status=status.HTTP_200_OK,
        )


@extend_schema(
    auth=[],
    tags=["Public - FAQs"],
    description="List FAQ categories with their questions and answers. No authentication required.",
)
class FAQCategoryPublicViewSet(SuccessEnvelopeMixin, ReadOnlyModelViewSet):
    serializer_class = FAQCategoryPublicSerializer
    permission_classes = []
    authentication_classes = []
    success_message = "FAQ categories retrieved successfully."

    def get_queryset(self):
        return FAQCategory.objects.prefetch_related("faqs").all()


@extend_schema(
    auth=[],
    tags=["Public - FAQs"],
    description="List or retrieve frequently asked questions. No authentication required.",
)
class FAQPublicViewSet(SuccessEnvelopeMixin, ReadOnlyModelViewSet):
    serializer_class = FAQPublicSerializer
    permission_classes = []
    authentication_classes = []
    success_message = "FAQs retrieved successfully."

    def get_queryset(self):
        queryset = FAQ.objects.select_related("category").all()
        category_id = self.request.query_params.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset


@extend_schema(tags=["Admin - FAQs"], description="Manage FAQ categories. Admin access only.")
class FAQCategoryAdminViewSet(SuccessEnvelopeMixin, ModelViewSet):
    serializer_class = FAQCategorySerializer
    permission_classes = [IsAdminUser]
    queryset = FAQCategory.objects.all()

    def get_success_message(self, request=None):
        if request and request.method == "POST":
            return "FAQ category created successfully."
        if request and request.method in ["PUT", "PATCH"]:
            return "FAQ category updated successfully."
        if request and request.method == "DELETE":
            return "FAQ category deleted successfully."
        return "FAQ category retrieved successfully."


@extend_schema(tags=["Admin - FAQs"], description="Manage FAQs. Admin access only.")
class FAQAdminViewSet(SuccessEnvelopeMixin, ModelViewSet):
    serializer_class = FAQSerializer
    permission_classes = [IsAdminUser]
    queryset = FAQ.objects.select_related("category").all()
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["category"]

    def get_success_message(self, request=None):
        if request and request.method == "POST":
            return "FAQ created successfully."
        if request and request.method in ["PUT", "PATCH"]:
            return "FAQ updated successfully."
        if request and request.method == "DELETE":
            return "FAQ deleted successfully."
        return "FAQ retrieved successfully."


@extend_schema(
    auth=[],
    tags=["Public - Blogs"],
    description=(
        "List and retrieve published blogs. Filter with category, min_views, "
        "max_views, and is_featured; order by views, title, or created_at. "
        "Retrieving a blog detail increments its view count."
    ),
)
class BlogPublicViewSet(SuccessEnvelopeMixin, ReadOnlyModelViewSet):
    serializer_class = BlogPublicSerializer
    permission_classes = []
    authentication_classes = []
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = BlogFilter
    ordering_fields = ["views", "title", "created_at"]
    ordering = ["-created_at"]
    success_message = "Blogs retrieved successfully."

    def get_queryset(self):
        return Blog.objects.filter(is_published=True).select_related("category")

    def retrieve(self, request, *args, **kwargs):
        from django.shortcuts import get_object_or_404

        blog = get_object_or_404(self.filter_queryset(self.get_queryset()), pk=kwargs["pk"])
        Blog.objects.filter(pk=blog.pk).update(views=F("views") + 1)
        blog.refresh_from_db(fields=["views"])
        serializer = self.get_serializer(blog)
        return Response(serializer.data)


@extend_schema(tags=["Admin - Blogs"], description="Manage blog categories. Admin access only.")
class BlogCategoryAdminViewSet(SuccessEnvelopeMixin, ModelViewSet):
    serializer_class = BlogCategorySerializer
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        return BlogCategory.objects.annotate(blogs_count=Count("blogs")).all()

    def get_success_message(self, request=None):
        if request and request.method == "POST":
            return "Blog category created successfully."
        if request and request.method in ["PUT", "PATCH"]:
            return "Blog category updated successfully."
        if request and request.method == "DELETE":
            return "Blog category deleted successfully."
        return "Blog categories retrieved successfully."


@extend_schema(tags=["Admin - Blogs"], description="Manage blogs. Admin access only.")
class BlogAdminViewSet(SuccessEnvelopeMixin, ModelViewSet):
    serializer_class = BlogSerializer
    permission_classes = [IsAdminUser]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = BlogFilter
    ordering_fields = ["views", "title", "created_at", "updated_at"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return Blog.objects.select_related("category").all()

    def get_success_message(self, request=None):
        if request and request.method == "POST":
            return "Blog created successfully."
        if request and request.method in ["PUT", "PATCH"]:
            return "Blog updated successfully."
        if request and request.method == "DELETE":
            return "Blog deleted successfully."
        return "Blogs retrieved successfully."


@extend_schema(
    auth=[],
    tags=["Public - Blogs"],
    description="List blog categories with counts of their published blogs.",
)
class BlogCategoryPublicViewSet(SuccessEnvelopeMixin, ReadOnlyModelViewSet):
    serializer_class = BlogCategoryPublicSerializer
    permission_classes = []
    authentication_classes = []
    success_message = "Blog categories retrieved successfully."

    def get_queryset(self):
        return BlogCategory.objects.annotate(
            blogs_count=Count("blogs", filter=Q(blogs__is_published=True))
        ).all()
