"""CMS models for site configuration and policies."""

from django.core.exceptions import ValidationError
from django.db import models

from apps.common.models import TimeStampedModel


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
        help_text="Cloudinary image URL or reference name"
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
        help_text="Section 1 description"
    )
    section1_image = models.CharField(
        max_length=500,
        blank=True,
        help_text="Section 1 image (Cloudinary URL or reference)"
    )
    
    # Section 2
    section2_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Section 2 title"
    )
    section2_description = models.TextField(
        blank=True,
        help_text="Section 2 description"
    )
    section2_image = models.CharField(
        max_length=500,
        blank=True,
        help_text="Section 2 image (Cloudinary URL or reference)"
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
        help_text="Subsection image (Cloudinary URL or reference)"
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
