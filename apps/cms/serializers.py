"""CMS serializers."""

from rest_framework import serializers

from .models import SiteConfiguration


class SocialMediaLinksSerializer(serializers.Serializer):
    """Nested serializer for social media links."""
    
    facebook = serializers.URLField(source='facebook_url', required=False, allow_blank=True)
    instagram = serializers.URLField(source='instagram_url', required=False, allow_blank=True)
    tiktok = serializers.URLField(source='tiktok_url', required=False, allow_blank=True)
    pinterest = serializers.URLField(source='pinterest_url', required=False, allow_blank=True)


class SiteConfigurationSerializer(serializers.ModelSerializer):
    """Site configuration serializer with nested social media links."""
    
    social = SocialMediaLinksSerializer(source='*', required=False, allow_null=True)
    
    class Meta:
        model = SiteConfiguration
        fields = [
            'id',
            'company_intro',
            'email',
            'phone',
            'whatsapp',
            'address',
            'map_url',
            'social',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Format response with nested social object."""
        data = super().to_representation(instance)
        # Group social media links under 'social' key
        social_data = data.pop('social', {})
        data['social'] = social_data
        return data
    
    def update(self, instance, validated_data):
        """Handle updates including nested social data."""
        # Update all simple fields
        for field in ['company_intro', 'email', 'phone', 'whatsapp', 'address', 'map_url']:
            if field in validated_data:
                setattr(instance, field, validated_data[field])
        
        # Update social media fields
        if 'facebook_url' in validated_data:
            instance.facebook_url = validated_data['facebook_url']
        if 'instagram_url' in validated_data:
            instance.instagram_url = validated_data['instagram_url']
        if 'tiktok_url' in validated_data:
            instance.tiktok_url = validated_data['tiktok_url']
        if 'pinterest_url' in validated_data:
            instance.pinterest_url = validated_data['pinterest_url']
        
        instance.save()
        return instance


class SiteConfigurationPublicSerializer(serializers.ModelSerializer):
    """Public read-only serializer for site configuration."""
    
    social = SocialMediaLinksSerializer(source='*', read_only=True)
    
    class Meta:
        model = SiteConfiguration
        fields = [
            'company_intro',
            'email',
            'phone',
            'whatsapp',
            'address',
            'map_url',
            'social',
        ]
    
    def to_representation(self, instance):
        """Format response with nested social object."""
        data = super().to_representation(instance)
        # Group social media links under 'social' key
        social_data = data.pop('social', {})
        data['social'] = social_data
        return data



from .models import Policy


class PolicySerializer(serializers.ModelSerializer):
    """Policy serializer for admin operations."""
    
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Policy
        fields = [
            'id',
            'type',
            'type_display',
            'title',
            'content',
            'is_active',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PolicyPublicSerializer(serializers.ModelSerializer):
    """Public read-only serializer for policies."""
    
    type_display = serializers.CharField(source='get_type_display', read_only=True)
    
    class Meta:
        model = Policy
        fields = [
            'id',
            'type',
            'type_display',
            'title',
            'content',
        ]



from .models import OurMakers, TeamMember


class TeamMemberSerializer(serializers.ModelSerializer):
    """Team member serializer."""
    
    class Meta:
        model = TeamMember
        fields = [
            'id',
            'name',
            'image',
            'role',
            'intro',
            'sort_order',
            'is_active',
        ]


class TeamMemberPublicSerializer(serializers.ModelSerializer):
    """Public read-only serializer for team members."""
    
    class Meta:
        model = TeamMember
        fields = [
            'name',
            'image',
            'role',
            'intro',
        ]


class OurMakersSerializer(serializers.ModelSerializer):
    """Our Makers page serializer with nested team members."""
    
    team_members = TeamMemberSerializer(many=True, read_only=True)
    
    class Meta:
        model = OurMakers
        fields = [
            'id',
            'title',
            'description',
            'team_members',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OurMakersPublicSerializer(serializers.ModelSerializer):
    """Public read-only serializer for Our Makers page."""
    
    team_members = TeamMemberPublicSerializer(many=True, read_only=True)
    
    class Meta:
        model = OurMakers
        fields = [
            'title',
            'description',
            'team_members',
        ]
    
    def to_representation(self, instance):
        """Only include active team members in public response."""
        data = super().to_representation(instance)
        # Filter to only active members
        active_members = [
            member for member in instance.team_members.filter(is_active=True).order_by('sort_order', 'name')
        ]
        data['team_members'] = TeamMemberPublicSerializer(active_members, many=True).data
        return data



from .models import OurStory, StorySubsection


class StorySubsectionSerializer(serializers.ModelSerializer):
    """Story subsection serializer."""
    
    class Meta:
        model = StorySubsection
        fields = [
            'id',
            'title',
            'image',
            'description',
            'sort_order',
            'is_active',
        ]


class StorySubsectionPublicSerializer(serializers.ModelSerializer):
    """Public read-only serializer for subsections."""
    
    class Meta:
        model = StorySubsection
        fields = [
            'title',
            'image',
            'description',
        ]


class Section1Serializer(serializers.Serializer):
    """Nested serializer for Section 1."""
    title = serializers.CharField(source='section1_title')
    description = serializers.CharField(source='section1_description')
    image = serializers.CharField(source='section1_image')


class Section2Serializer(serializers.Serializer):
    """Nested serializer for Section 2."""
    title = serializers.CharField(source='section2_title')
    description = serializers.CharField(source='section2_description')
    image = serializers.CharField(source='section2_image')


class Section3Serializer(serializers.Serializer):
    """Nested serializer for Section 3 with subsections."""
    title = serializers.CharField(source='section3_title')
    subsections = serializers.SerializerMethodField()
    
    def get_subsections(self, obj):
        # For admin, include all subsections
        subsections = obj.section3_subsections.all().order_by('sort_order', 'created_at')
        return StorySubsectionSerializer(subsections, many=True).data


class Section3PublicSerializer(serializers.Serializer):
    """Public nested serializer for Section 3 with subsections."""
    title = serializers.CharField(source='section3_title')
    subsections = serializers.SerializerMethodField()
    
    def get_subsections(self, obj):
        # For public, only active subsections
        subsections = obj.section3_subsections.filter(is_active=True).order_by('sort_order', 'created_at')
        return StorySubsectionPublicSerializer(subsections, many=True).data


class OurStorySerializer(serializers.ModelSerializer):
    """Our Story page serializer with nested sections."""
    
    section1 = Section1Serializer(source='*', read_only=True)
    section2 = Section2Serializer(source='*', read_only=True)
    section3 = Section3Serializer(source='*', read_only=True)
    
    class Meta:
        model = OurStory
        fields = [
            'id',
            'title',
            'description',
            'section1',
            'section2',
            'section3',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OurStoryPublicSerializer(serializers.ModelSerializer):
    """Public read-only serializer for Our Story page."""
    
    section1 = Section1Serializer(source='*', read_only=True)
    section2 = Section2Serializer(source='*', read_only=True)
    section3 = Section3PublicSerializer(source='*', read_only=True)
    
    class Meta:
        model = OurStory
        fields = [
            'title',
            'description',
            'section1',
            'section2',
            'section3',
        ]



from .models import OurSustainability, SustainabilitySection


class SustainabilitySectionSerializer(serializers.ModelSerializer):
    """Sustainability section serializer."""
    
    class Meta:
        model = SustainabilitySection
        fields = [
            'id',
            'title',
            'description',
            'image',
            'sort_order',
            'is_active',
        ]


class SustainabilitySectionPublicSerializer(serializers.ModelSerializer):
    """Public read-only serializer for sustainability sections."""
    
    class Meta:
        model = SustainabilitySection
        fields = [
            'title',
            'description',
            'image',
        ]


class OurSustainabilitySerializer(serializers.ModelSerializer):
    """Our Sustainability page serializer with nested sections."""
    
    sections = SustainabilitySectionSerializer(many=True, read_only=True)
    
    class Meta:
        model = OurSustainability
        fields = [
            'id',
            'title',
            'description',
            'sections',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OurSustainabilityPublicSerializer(serializers.ModelSerializer):
    """Public read-only serializer for Our Sustainability page."""
    
    sections = serializers.SerializerMethodField()
    
    class Meta:
        model = OurSustainability
        fields = [
            'title',
            'description',
            'sections',
        ]
    
    def get_sections(self, obj):
        """Only include active sections in public response."""
        active_sections = obj.sections.filter(is_active=True).order_by('sort_order', 'created_at')
        return SustainabilitySectionPublicSerializer(active_sections, many=True).data
