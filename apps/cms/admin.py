"""CMS admin configuration."""

from django.contrib import admin

from .models import SiteConfiguration


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for site configuration."""
    
    list_display = ['__str__', 'email', 'phone', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Contact Information', {
            'fields': ('email', 'phone', 'whatsapp'),
        }),
        ('Address & Location', {
            'fields': ('address', 'map_url'),
        }),
        ('Social Media Links', {
            'fields': ('facebook_url', 'instagram_url', 'tiktok_url', 'pinterest_url'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        """Only allow one instance (singleton)."""
        return not SiteConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of the configuration."""
        return False
