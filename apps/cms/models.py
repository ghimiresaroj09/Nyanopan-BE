"""CMS models for site configuration and policies."""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import TimeStampedModel
from apps.common.storages import image_storage
from apps.common.validators import validate_image_upload


def _cms_image_path(folder, filename):
    """Generate upload path for CMS images."""
    base = (getattr(settings, "CLOUDINARY_UPLOAD_FOLDER", "") or "ecommerce").strip("/")
    ext = filename.rsplit(".", 1)[-1].lower() if "." in (filename or "") else ""
    name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    return f"{base}/cms/{folder}/{name}"


def team_member_image_path(instance, filename):
    return _cms_image_path("team-members", filename)


def story_image_path(instance, filename):
    return _cms_image_path("story", filename)


def story_subsection_image_path(instance, filename):
    return _cms_image_path("story-subsections", filename)


def sustainability_section_image_path(instance, filename):
    return _cms_image_path("sustainability", filename)


class SiteConfiguration(TimeStampedModel):
    """Site-wide configuration settings (singleton model).
    
    Only one instance should exist. Contains contact information,
    social media links, and other global settings.
    """
    
    # Override parent's UUID field with integer PK for singleton pattern
    id = models.AutoField(primary_key=True)

    # Company Information
    company_intro = models.TextField(
        blank=True,
        help_text="Company introduction or about us text"
    )
    
    # Contact Information
    email = models.EmailField(
        max_length=255,
        blank=True,
        help_text="Primary contact email address"
    )
    phone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Primary phone number with country code (e.g., +977-1234567890)"
    )
    whatsapp = models.CharField(
        max_length=50,
        blank=True,
        help_text="WhatsApp number with country code (e.g., +977-1234567890)"
    )
    
    # Address
    address = models.TextField(
        blank=True,
        help_text="Physical address of the business"
    )
    map_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="Google Maps URL or embedded map link"
    )
    
    # Social Media Links
    facebook_url = models.URLField(
        max_length=255,
        blank=True,
        help_text="Facebook page URL"
    )
    instagram_url = models.URLField(
        max_length=255,
        blank=True,
        help_text="Instagram profile URL"
    )
    tiktok_url = models.URLField(
        max_length=255,
        blank=True,
        help_text="TikTok profile URL"
    )
    pinterest_url = models.URLField(
        max_length=255,
        blank=True,
        help_text="Pinterest profile URL"
    )
    
    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"
        db_table = "cms_site_configuration"
    
    def __str__(self):
        return "Site Configuration"
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)."""
        if not self.pk and SiteConfiguration.objects.exists():
            raise ValidationError(
                "Only one Site Configuration instance is allowed. "
                "Please update the existing configuration."
            )
        super().save(*args, **kwargs)
    
    @classmethod
    def get_config(cls):
        """Get or create the singleton configuration instance."""
        config, created = cls.objects.get_or_create(pk=1)
        return config



class PolicyType(models.TextChoices):
    """Types of policies available."""
    SHIPPING = "SHIPPING", "Shipping"
    EXCHANGES_RETURNS = "EXCHANGES_RETURNS", "Exchanges & Returns"
    PRIVACY_POLICY = "PRIVACY_POLICY", "Privacy Policy"
    TERMS_CONDITIONS = "TERMS_CONDITIONS", "Terms and Conditions"


class Policy(TimeStampedModel):
    """Policy documents (shipping, returns, privacy, terms, etc.).
    
    Each policy type can only have one active document.
    Content is stored as rich text (HTML from frontend editor).
    """
    
    type = models.CharField(
        max_length=50,
        choices=PolicyType.choices,
        unique=True,
        db_index=True,
        help_text="Type of policy document"
    )
    title = models.CharField(
        max_length=255,
        help_text="Policy title (e.g., 'Shipping Policy', 'Privacy Policy')"
    )
    content = models.TextField(
        help_text="Policy content in HTML format (from rich text editor)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this policy is currently active and visible"
    )
    
    class Meta:
        verbose_name = "Policy"
        verbose_name_plural = "Policies"
        db_table = "cms_policy"
        ordering = ['type']
    
    def __str__(self):
        return f"{self.get_type_display()}"
    
    def save(self, *args, **kwargs):
        """Ensure title is set if empty."""
        if not self.title:
            self.title = self.get_type_display()
        super().save(*args, **kwargs)



class OurMakers(TimeStampedModel):
    """Our Makers/Team page (singleton model).
    
    Displays team members/makers information on the website.
    Only one instance should exist.
    """
    
    # Override parent's UUID field with integer PK for singleton pattern
    id = models.AutoField(primary_key=True)
    
    title = models.CharField(
        max_length=255,
        default="Our Makers",
        help_text="Page title (e.g., 'Meet Our Makers', 'Our Team')"
    )
    description = models.TextField(
        blank=True,
        help_text="Introduction text about the makers/team"
    )
    
    class Meta:
        verbose_name = "Our Makers"
        verbose_name_plural = "Our Makers"
        db_table = "cms_our_makers"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)."""
        if not self.pk and OurMakers.objects.exists():
            raise ValidationError(
                "Only one Our Makers instance is allowed. "
                "Please update the existing page."
            )
        super().save(*args, **kwargs)
    
    @classmethod
    def get_page(cls):
        """Get or create the singleton page instance."""
        page, created = cls.objects.get_or_create(pk=1)
        return page


class TeamMember(TimeStampedModel):
    """Individual team member/maker information."""
    
    our_makers = models.ForeignKey(
        OurMakers,
        on_delete=models.CASCADE,
        related_name='team_members',
        help_text="Our Makers page this member belongs to"
    )
    name = models.CharField(
        max_length=255,
        help_text="Team member's full name"
    )
    image = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text="Team member image URL (Cloudinary)"
    )
    role = models.CharField(
        max_length=255,
        help_text="Job title or role (e.g., 'Master Craftsman', 'Designer')"
    )
    intro = models.TextField(
        help_text="Brief introduction or bio"
    )
    sort_order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this member is currently displayed"
    )
    
    class Meta:
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"
        db_table = "cms_team_member"
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.role}"



class OurStory(TimeStampedModel):
    """Our Story page (singleton model).
    
    Displays company story with multiple sections.
    Only one instance should exist.
    """
    
    # Override parent's UUID field with integer PK for singleton pattern
    id = models.AutoField(primary_key=True)
    
    # Main page content
    title = models.CharField(
        max_length=255,
        default="Our Story",
        help_text="Main page title"
    )
    description = models.TextField(
        blank=True,
        help_text="Main introduction text"
    )
    
    # Section 1
    section1_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Section 1 title"
    )
    section1_description = models.TextField(
        blank=True,
        default='',
        help_text="Section 1 description"
    )
    section1_image = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text="Section 1 image URL (Cloudinary)"
    )
    
    # Section 2
    section2_title = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Section 2 title"
    )
    section2_description = models.TextField(
        blank=True,
        default='',
        help_text="Section 2 description"
    )
    section2_image = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text="Section 2 image URL (Cloudinary)"
    )
    
    # Section 3 title (subsections stored in StorySubsection model)
    section3_title = models.CharField(
        max_length=255,
        blank=True,
        default="Our Journey",
        help_text="Section 3 title (has subsections)"
    )
    
    class Meta:
        verbose_name = "Our Story"
        verbose_name_plural = "Our Story"
        db_table = "cms_our_story"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)."""
        if not self.pk and OurStory.objects.exists():
            raise ValidationError(
                "Only one Our Story instance is allowed. "
                "Please update the existing page."
            )
        super().save(*args, **kwargs)
    
    @classmethod
    def get_page(cls):
        """Get or create the singleton page instance."""
        page, created = cls.objects.get_or_create(pk=1)
        return page


class StorySubsection(TimeStampedModel):
    """Subsections for Section 3 of Our Story page."""
    
    our_story = models.ForeignKey(
        OurStory,
        on_delete=models.CASCADE,
        related_name='section3_subsections',
        help_text="Our Story page this subsection belongs to"
    )
    title = models.CharField(
        max_length=255,
        help_text="Subsection title"
    )
    image = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text="Subsection image URL (Cloudinary)"
    )
    description = models.TextField(
        help_text="Subsection description"
    )
    sort_order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this subsection is currently displayed"
    )
    
    class Meta:
        verbose_name = "Story Subsection"
        verbose_name_plural = "Story Subsections"
        db_table = "cms_story_subsection"
        ordering = ['sort_order', 'created_at']
    
    def __str__(self):
        return self.title



class OurSustainability(TimeStampedModel):
    """Our Sustainability page (singleton model).
    
    Displays sustainability initiatives and commitments.
    Only one instance should exist.
    """
    
    # Override parent's UUID field with integer PK for singleton pattern
    id = models.AutoField(primary_key=True)
    
    title = models.CharField(
        max_length=255,
        default="Our Sustainability",
        help_text="Page title"
    )
    description = models.TextField(
        blank=True,
        help_text="Introduction text about sustainability commitment"
    )
    
    class Meta:
        verbose_name = "Our Sustainability"
        verbose_name_plural = "Our Sustainability"
        db_table = "cms_our_sustainability"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)."""
        if not self.pk and OurSustainability.objects.exists():
            raise ValidationError(
                "Only one Our Sustainability instance is allowed. "
                "Please update the existing page."
            )
        super().save(*args, **kwargs)
    
    @classmethod
    def get_page(cls):
        """Get or create the singleton page instance."""
        page, created = cls.objects.get_or_create(pk=1)
        return page


class SustainabilitySection(TimeStampedModel):
    """Sections for Our Sustainability page."""
    
    our_sustainability = models.ForeignKey(
        OurSustainability,
        on_delete=models.CASCADE,
        related_name='sections',
        help_text="Our Sustainability page this section belongs to"
    )
    title = models.CharField(
        max_length=255,
        help_text="Section title"
    )
    description = models.TextField(
        help_text="Section description"
    )
    image = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text="Section image URL (Cloudinary)"
    )
    sort_order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this section is currently displayed"
    )
    
    class Meta:
        verbose_name = "Sustainability Section"
        verbose_name_plural = "Sustainability Sections"
        db_table = "cms_sustainability_section"
        ordering = ['sort_order', 'created_at']
    
    def __str__(self):
        return self.title



# ============================================================================
# HOMEPAGE MODELS
# ============================================================================

class Homepage(TimeStampedModel):
    """Homepage content (singleton model).
    
    Contains three main sections for homepage display.
    Only one instance should exist.
    """
    
    # Override parent's UUID field with integer PK for singleton pattern
    id = models.AutoField(primary_key=True)
    
    # Section 1
    section1_tag = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Section 1 tag/label"
    )
    section1_image = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text="Section 1 image URL (Cloudinary)"
    )
    section1_title = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Section 1 title"
    )
    section1_description = models.TextField(
        blank=True,
        default='',
        help_text="Section 1 description"
    )
    section1_quote = models.TextField(
        blank=True,
        default='',
        help_text="Section 1 quote"
    )
    
    # Section 2
    section2_tag = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Section 2 tag/label"
    )
    section2_title = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Section 2 title"
    )
    section2_description = models.TextField(
        blank=True,
        default='',
        help_text="Section 2 description"
    )
    section2_image = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text="Section 2 image URL (Cloudinary)"
    )
    section2_features = models.JSONField(
        default=list,
        blank=True,
        help_text="Array of feature objects with title and intro"
    )
    
    # Section 3
    section3_tag = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Section 3 tag/label"
    )
    section3_title = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text="Section 3 title"
    )
    section3_image = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text="Section 3 image URL (Cloudinary)"
    )
    section3_description = models.TextField(
        blank=True,
        default='',
        help_text="Section 3 description"
    )
    
    class Meta:
        verbose_name = "Homepage"
        verbose_name_plural = "Homepage"
        db_table = "cms_homepage"
    
    def __str__(self):
        return "Homepage Content"
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)."""
        if not self.pk and Homepage.objects.exists():
            raise ValidationError(
                "Only one Homepage instance is allowed. "
                "Please update the existing homepage."
            )
        super().save(*args, **kwargs)
    
    @classmethod
    def get_homepage(cls):
        """Get or create the singleton homepage instance."""
        homepage, created = cls.objects.get_or_create(pk=1)
        return homepage


class HomepageCollections(TimeStampedModel):
    """Homepage Collections section (singleton model).
    
    Contains collections showcase for homepage.
    Only one instance should exist.
    """
    
    # Override parent's UUID field with integer PK for singleton pattern
    id = models.AutoField(primary_key=True)
    
    tag = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="Collections section tag/label"
    )
    title = models.CharField(
        max_length=255,
        default="Our Collections",
        help_text="Collections section title"
    )
    description = models.TextField(
        blank=True,
        default='',
        help_text="Collections section description"
    )
    
    class Meta:
        verbose_name = "Homepage Collections"
        verbose_name_plural = "Homepage Collections"
        db_table = "cms_homepage_collections"
    
    def __str__(self):
        return "Homepage Collections"
    
    def save(self, *args, **kwargs):
        """Ensure only one instance exists (singleton pattern)."""
        if not self.pk and HomepageCollections.objects.exists():
            raise ValidationError(
                "Only one Homepage Collections instance is allowed. "
                "Please update the existing instance."
            )
        super().save(*args, **kwargs)
    
    @classmethod
    def get_collections_page(cls):
        """Get or create the singleton collections instance."""
        page, created = cls.objects.get_or_create(pk=1)
        return page


class Collection(TimeStampedModel):
    """Individual collection item for homepage."""
    
    homepage_collections = models.ForeignKey(
        HomepageCollections,
        on_delete=models.CASCADE,
        related_name='collections',
        help_text="Homepage Collections page this item belongs to"
    )
    image = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text="Collection image URL (Cloudinary)"
    )
    name = models.CharField(
        max_length=255,
        help_text="Collection name"
    )
    intro = models.TextField(
        help_text="Collection introduction/description"
    )
    link = models.CharField(
        max_length=255,
        help_text="Internal link path (e.g., /inside, /outdoor)"
    )
    sort_order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this collection is currently displayed"
    )
    
    class Meta:
        verbose_name = "Collection"
        verbose_name_plural = "Collections"
        db_table = "cms_collection"
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name



# ============================================================================
# SUBSCRIPTION MODEL
# ============================================================================

class Subscription(TimeStampedModel):
    """Newsletter subscription model."""
    
    email = models.EmailField(
        max_length=255,
        unique=True,
        help_text="Subscriber email address"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether subscription is active"
    )
    subscribed_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Subscription date"
    )
    
    class Meta:
        verbose_name = "Subscription"
        verbose_name_plural = "Subscriptions"
        db_table = "cms_subscription"
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return self.email



# ============================================================================
# CONTACT US MODEL
# ============================================================================

class ContactMessage(TimeStampedModel):
    """Contact form submission model."""
    
    class StatusChoices(models.TextChoices):
        NEW = 'NEW', 'New'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        RESOLVED = 'RESOLVED', 'Resolved'
        CLOSED = 'CLOSED', 'Closed'
    
    name = models.CharField(
        max_length=255,
        help_text="Sender's full name"
    )
    email = models.EmailField(
        max_length=255,
        help_text="Sender's email address"
    )
    phone = models.CharField(
        max_length=50,
        blank=True,
        default='',
        help_text="Sender's phone number (optional)"
    )
    subject = models.CharField(
        max_length=255,
        help_text="Message subject"
    )
    message = models.TextField(
        help_text="Message content"
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.NEW,
        help_text="Message status"
    )
    admin_notes = models.TextField(
        blank=True,
        default='',
        help_text="Internal admin notes"
    )
    
    class Meta:
        verbose_name = "Contact Message"
        verbose_name_plural = "Contact Messages"
        db_table = "cms_contact_message"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.subject}"
