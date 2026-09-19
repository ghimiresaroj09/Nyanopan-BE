"""CMS admin configuration."""

from django.contrib import admin

from .models import OurMakers, Policy, SiteConfiguration, TeamMember


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for site configuration."""
    
    list_display = ['__str__', 'email', 'phone', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Company Information', {
            'fields': ('company_intro',),
        }),
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



@admin.register(Policy)
class PolicyAdmin(admin.ModelAdmin):
    """Admin interface for policies."""
    
    list_display = ['type', 'title', 'is_active', 'created_at', 'updated_at']
    list_filter = ['type', 'is_active', 'created_at']
    search_fields = ['title', 'content']
    ordering = ['type']
    
    fieldsets = (
        ('Policy Information', {
            'fields': ('type', 'title', 'is_active'),
        }),
        ('Content', {
            'fields': ('content',),
            'description': 'Content in HTML format from rich text editor',
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']



class TeamMemberInline(admin.TabularInline):
    """Inline admin for team members."""
    model = TeamMember
    extra = 1
    fields = ['name', 'role', 'image', 'intro', 'sort_order', 'is_active']
    ordering = ['sort_order', 'name']


@admin.register(OurMakers)
class OurMakersAdmin(admin.ModelAdmin):
    """Admin interface for Our Makers page."""
    
    list_display = ['title', 'created_at', 'updated_at']
    inlines = [TeamMemberInline]
    
    fieldsets = (
        ('Page Information', {
            'fields': ('title', 'description'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        """Only allow one instance (singleton)."""
        return not OurMakers.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of the page."""
        return False


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    """Admin interface for team members."""
    
    list_display = ['name', 'role', 'sort_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'role', 'intro']
    ordering = ['sort_order', 'name']
    
    fieldsets = (
        ('Member Information', {
            'fields': ('our_makers', 'name', 'role', 'image'),
        }),
        ('Biography', {
            'fields': ('intro',),
        }),
        ('Display Settings', {
            'fields': ('sort_order', 'is_active'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
