"""CMS models for site configuration."""

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
