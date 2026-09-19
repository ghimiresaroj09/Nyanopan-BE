"""CMS admin configuration."""

from django.contrib import admin

from . import models


@admin.register(models.SiteConfiguration)
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



@admin.register(models.Policy)
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
    model = models.TeamMember
    extra = 1
    fields = ['name', 'role', 'image', 'intro', 'sort_order', 'is_active']
    ordering = ['sort_order', 'name']


@admin.register(models.OurMakers)
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


@admin.register(models.TeamMember)
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



class StorySubsectionInline(admin.TabularInline):
    """Inline admin for story subsections."""
    model = models.StorySubsection
    extra = 1
    fields = ['title', 'image', 'description', 'sort_order', 'is_active']
    ordering = ['sort_order', 'created_at']


@admin.register(models.OurStory)
class OurStoryAdmin(admin.ModelAdmin):
    """Admin interface for Our Story page."""
    
    list_display = ['title', 'created_at', 'updated_at']
    inlines = [StorySubsectionInline]
    
    fieldsets = (
        ('Main Content', {
            'fields': ('title', 'description'),
        }),
        ('Section 1', {
            'fields': ('section1_title', 'section1_description', 'section1_image'),
        }),
        ('Section 2', {
            'fields': ('section2_title', 'section2_description', 'section2_image'),
        }),
        ('Section 3', {
            'fields': ('section3_title',),
            'description': 'Subsections are managed below or in the Story Subsections admin.',
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def has_add_permission(self, request):
        """Only allow one instance (singleton)."""
        return not OurStory.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of the page."""
        return False


@admin.register(models.StorySubsection)
class StorySubsectionAdmin(admin.ModelAdmin):
    """Admin interface for story subsections."""
    
    list_display = ['title', 'sort_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['sort_order', 'created_at']
    
    fieldsets = (
        ('Subsection Content', {
            'fields': ('our_story', 'title', 'image', 'description'),
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



class SustainabilitySectionInline(admin.TabularInline):
    """Inline admin for sustainability sections."""
    model = models.SustainabilitySection
    extra = 1
    fields = ['title', 'description', 'image', 'sort_order', 'is_active']
    ordering = ['sort_order', 'created_at']


@admin.register(models.OurSustainability)
class OurSustainabilityAdmin(admin.ModelAdmin):
    """Admin interface for Our Sustainability page."""
    
    list_display = ['title', 'created_at', 'updated_at']
    inlines = [SustainabilitySectionInline]
    
    fieldsets = (
        ('Page Content', {
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
        return not OurSustainability.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of the page."""
        return False


@admin.register(models.SustainabilitySection)
class SustainabilitySectionAdmin(admin.ModelAdmin):
    """Admin interface for sustainability sections."""
    
    list_display = ['title', 'sort_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'description']
    ordering = ['sort_order', 'created_at']
    
    fieldsets = (
        ('Section Content', {
            'fields': ('our_sustainability', 'title', 'description', 'image'),
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



# Homepage models
@admin.register(models.Homepage)
class HomepageAdmin(admin.ModelAdmin):
    list_display = ['id', 'created_at', 'updated_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not models.Homepage.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of singleton
        return False


@admin.register(models.HomepageCollections)
class HomepageCollectionsAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'tag', 'created_at']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    def has_add_permission(self, request):
        # Only allow one instance
        return not models.HomepageCollections.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of singleton
        return False


@admin.register(models.Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'link', 'sort_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'intro', 'link']
    ordering = ['sort_order', 'name']



@admin.register(models.Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'subscribed_at', 'created_at']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email']
    readonly_fields = ['subscribed_at', 'created_at', 'updated_at']
    ordering = ['-subscribed_at']
    
    fieldsets = (
        ('Subscription Info', {
            'fields': ('email', 'is_active'),
        }),
        ('Timestamps', {
            'fields': ('subscribed_at', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
