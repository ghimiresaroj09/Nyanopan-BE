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
    
    our_makers = serializers.PrimaryKeyRelatedField(
        queryset=OurMakers.objects.all(),
        required=False,
        help_text="Our Makers page (defaults to singleton page if not provided)"
    )
    
    class Meta:
        model = TeamMember
        fields = [
            'id',
            'our_makers',
            'name',
            'image',
            'role',
            'intro',
            'sort_order',
            'is_active',
        ]
        read_only_fields = ['id']
    
    def create(self, validated_data):
        # If our_makers not provided, use the singleton page
        if 'our_makers' not in validated_data:
            validated_data['our_makers'] = OurMakers.get_page()
        return super().create(validated_data)


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
    
    # Override image field to accept URL strings instead of binary files
    image = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Cloudinary image URL"
    )
    
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
        read_only_fields = ['id']


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
    title = serializers.CharField(source='section1_title', required=False, allow_blank=True)
    description = serializers.CharField(source='section1_description', required=False, allow_blank=True)
    image = serializers.CharField(source='section1_image', required=False, allow_blank=True, allow_null=True)


class Section2Serializer(serializers.Serializer):
    """Nested serializer for Section 2."""
    title = serializers.CharField(source='section2_title', required=False, allow_blank=True)
    description = serializers.CharField(source='section2_description', required=False, allow_blank=True)
    image = serializers.CharField(source='section2_image', required=False, allow_blank=True, allow_null=True)


class Section3Serializer(serializers.Serializer):
    """Nested serializer for Section 3 with subsections."""
    title = serializers.CharField(source='section3_title', required=False, allow_blank=True)
    subsections = StorySubsectionSerializer(source='section3_subsections', many=True, read_only=False, required=False)


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
    
    section1 = Section1Serializer(source='*', required=False)
    section2 = Section2Serializer(source='*', required=False)
    section3 = Section3Serializer(source='*', required=False)
    
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
    
    def update(self, instance, validated_data):
        """Handle nested subsections update."""
        # Update simple fields
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        
        # Update section1 fields (check both nested and flat formats)
        instance.section1_title = validated_data.get('section1_title', instance.section1_title)
        instance.section1_description = validated_data.get('section1_description', instance.section1_description)
        section1_image = validated_data.get('section1_image')
        if section1_image is not None:
            instance.section1_image = section1_image if section1_image != '' else None
        
        # Update section2 fields
        instance.section2_title = validated_data.get('section2_title', instance.section2_title)
        instance.section2_description = validated_data.get('section2_description', instance.section2_description)
        section2_image = validated_data.get('section2_image')
        if section2_image is not None:
            instance.section2_image = section2_image if section2_image != '' else None
        
        # Update section3 title
        instance.section3_title = validated_data.get('section3_title', instance.section3_title)
        
        # Handle subsections if provided
        subsections_data = validated_data.get('section3_subsections')
        if subsections_data is not None:
            # Get existing subsection IDs
            existing_ids = set()
            
            for subsection_data in subsections_data:
                subsection_id = subsection_data.get('id')
                
                # Clean up empty image strings
                if 'image' in subsection_data and subsection_data['image'] == '':
                    subsection_data['image'] = None
                
                if subsection_id:
                    # Update existing
                    StorySubsection.objects.filter(id=subsection_id, our_story=instance).update(**{
                        k: v for k, v in subsection_data.items() if k != 'id'
                    })
                    existing_ids.add(subsection_id)
                else:
                    # Create new
                    new_subsection = StorySubsection.objects.create(
                        our_story=instance,
                        **subsection_data
                    )
                    existing_ids.add(new_subsection.id)
            
            # Delete subsections not in the provided list (optional - comment out if you don't want auto-delete)
            # instance.section3_subsections.exclude(id__in=existing_ids).delete()
        
        instance.save()
        return instance


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
    
    # Override image field to accept URL strings instead of binary files
    image = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Cloudinary image URL"
    )
    
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
        read_only_fields = ['id']


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
    
    sections = SustainabilitySectionSerializer(many=True, read_only=False, required=False)
    
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
    
    def update(self, instance, validated_data):
        """Handle nested sections update."""
        # Update simple fields
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        
        # Handle sections if provided
        sections_data = validated_data.get('sections')
        if sections_data is not None:
            # Get existing section IDs
            existing_ids = set()
            
            for section_data in sections_data:
                section_id = section_data.get('id')
                
                # Clean up empty image strings
                if 'image' in section_data and section_data['image'] == '':
                    section_data['image'] = None
                
                if section_id:
                    # Update existing
                    SustainabilitySection.objects.filter(id=section_id, our_sustainability=instance).update(**{
                        k: v for k, v in section_data.items() if k != 'id'
                    })
                    existing_ids.add(section_id)
                else:
                    # Create new
                    new_section = SustainabilitySection.objects.create(
                        our_sustainability=instance,
                        **section_data
                    )
                    existing_ids.add(new_section.id)
            
            # Delete sections not in the provided list (optional - comment out if you don't want auto-delete)
            # instance.sections.exclude(id__in=existing_ids).delete()
        
        instance.save()
        return instance


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
