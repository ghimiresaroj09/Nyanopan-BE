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
            instance.section1_image = section1_image if section1_image != '' else ''
        
        # Update section2 fields
        instance.section2_title = validated_data.get('section2_title', instance.section2_title)
        instance.section2_description = validated_data.get('section2_description', instance.section2_description)
        section2_image = validated_data.get('section2_image')
        if section2_image is not None:
            instance.section2_image = section2_image if section2_image != '' else ''
        
        # Update section3 title
        instance.section3_title = validated_data.get('section3_title', instance.section3_title)
        
        # Handle subsections if provided
        subsections_data = validated_data.get('section3_subsections')
        if subsections_data is not None:
            # If no subsections have IDs, replace all (delete old, create new)
            has_any_ids = any('id' in item for item in subsections_data)
            
            if not has_any_ids:
                # Replace mode: delete all existing and create new ones
                instance.section3_subsections.all().delete()
                for subsection_data in subsections_data:
                    # Clean up empty image strings
                    if 'image' in subsection_data and subsection_data['image'] == '':
                        subsection_data['image'] = ''
                    StorySubsection.objects.create(
                        our_story=instance,
                        **subsection_data
                    )
            else:
                # Update/Create mode: match by ID
                existing_ids = set()
                for subsection_data in subsections_data:
                    subsection_id = subsection_data.get('id')
                    
                    # Clean up empty image strings
                    if 'image' in subsection_data and subsection_data['image'] == '':
                        subsection_data['image'] = ''
                    
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
                
                # Optionally delete subsections not in the provided list
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
            # If no sections have IDs, replace all (delete old, create new)
            has_any_ids = any('id' in item for item in sections_data)
            
            if not has_any_ids:
                # Replace mode: delete all existing and create new ones
                instance.sections.all().delete()
                for section_data in sections_data:
                    # Clean up empty image strings
                    if 'image' in section_data and section_data['image'] == '':
                        section_data['image'] = ''
                    SustainabilitySection.objects.create(
                        our_sustainability=instance,
                        **section_data
                    )
            else:
                # Update/Create mode: match by ID
                existing_ids = set()
                for section_data in sections_data:
                    section_id = section_data.get('id')
                    
                    # Clean up empty image strings
                    if 'image' in section_data and section_data['image'] == '':
                        section_data['image'] = ''
                    
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
                
                # Optionally delete sections not in the provided list
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



# ============================================================================
# HOMEPAGE SERIALIZERS
# ============================================================================

from .models import Homepage, HomepageCollections, Collection


class Section1Serializer(serializers.Serializer):
    """Nested serializer for Homepage Section 1."""
    tag = serializers.CharField(source='section1_tag', required=False, allow_blank=True)
    image = serializers.CharField(source='section1_image', required=False, allow_blank=True)
    title = serializers.CharField(source='section1_title', required=False, allow_blank=True)
    description = serializers.CharField(source='section1_description', required=False, allow_blank=True)
    quote = serializers.CharField(source='section1_quote', required=False, allow_blank=True)


class FeatureSerializer(serializers.Serializer):
    """Serializer for section 2 features."""
    title = serializers.CharField()
    intro = serializers.CharField()


class Section2Serializer(serializers.Serializer):
    """Nested serializer for Homepage Section 2."""
    tag = serializers.CharField(source='section2_tag', required=False, allow_blank=True)
    title = serializers.CharField(source='section2_title', required=False, allow_blank=True)
    description = serializers.CharField(source='section2_description', required=False, allow_blank=True)
    image = serializers.CharField(source='section2_image', required=False, allow_blank=True)
    feature = FeatureSerializer(source='section2_features', many=True, required=False)


class Section3Serializer(serializers.Serializer):
    """Nested serializer for Homepage Section 3."""
    tag = serializers.CharField(source='section3_tag', required=False, allow_blank=True)
    title = serializers.CharField(source='section3_title', required=False, allow_blank=True)
    image = serializers.CharField(source='section3_image', required=False, allow_blank=True)
    description = serializers.CharField(source='section3_description', required=False, allow_blank=True)


class HomepageSerializer(serializers.ModelSerializer):
    """Homepage serializer with nested sections."""
    
    section1 = Section1Serializer(source='*', required=False)
    section2 = Section2Serializer(source='*', required=False)
    section3 = Section3Serializer(source='*', required=False)
    
    class Meta:
        model = Homepage
        fields = [
            'id',
            'section1',
            'section2',
            'section3',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        """Handle nested sections update."""
        # Update section 1 fields
        instance.section1_tag = validated_data.get('section1_tag', instance.section1_tag)
        instance.section1_image = validated_data.get('section1_image', instance.section1_image)
        instance.section1_title = validated_data.get('section1_title', instance.section1_title)
        instance.section1_description = validated_data.get('section1_description', instance.section1_description)
        instance.section1_quote = validated_data.get('section1_quote', instance.section1_quote)
        
        # Update section 2 fields
        instance.section2_tag = validated_data.get('section2_tag', instance.section2_tag)
        instance.section2_title = validated_data.get('section2_title', instance.section2_title)
        instance.section2_description = validated_data.get('section2_description', instance.section2_description)
        instance.section2_image = validated_data.get('section2_image', instance.section2_image)
        
        # Handle section2_features (array of feature objects)
        section2_features = validated_data.get('section2_features')
        if section2_features is not None:
            instance.section2_features = section2_features
        
        # Update section 3 fields
        instance.section3_tag = validated_data.get('section3_tag', instance.section3_tag)
        instance.section3_title = validated_data.get('section3_title', instance.section3_title)
        instance.section3_image = validated_data.get('section3_image', instance.section3_image)
        instance.section3_description = validated_data.get('section3_description', instance.section3_description)
        
        instance.save()
        return instance


class HomepagePublicSerializer(serializers.ModelSerializer):
    """Public read-only serializer for Homepage."""
    
    section1 = Section1Serializer(source='*', read_only=True)
    section2 = Section2Serializer(source='*', read_only=True)
    section3 = Section3Serializer(source='*', read_only=True)
    
    class Meta:
        model = Homepage
        fields = [
            'section1',
            'section2',
            'section3',
        ]


class CollectionSerializer(serializers.ModelSerializer):
    """Collection serializer."""
    
    # Override image field to accept URL strings
    image = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        help_text="Collection image URL (Cloudinary)"
    )
    
    class Meta:
        model = Collection
        fields = [
            'id',
            'image',
            'name',
            'intro',
            'link',
            'sort_order',
            'is_active',
        ]
        read_only_fields = ['id']


class CollectionPublicSerializer(serializers.ModelSerializer):
    """Public read-only serializer for collections."""
    
    class Meta:
        model = Collection
        fields = [
            'image',
            'name',
            'intro',
            'link',
        ]


class HomepageCollectionsSerializer(serializers.ModelSerializer):
    """Homepage Collections serializer with nested collections."""
    
    collections = CollectionSerializer(many=True, read_only=False, required=False)
    
    class Meta:
        model = HomepageCollections
        fields = [
            'id',
            'tag',
            'title',
            'description',
            'collections',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        """Handle nested collections update."""
        # Update simple fields
        instance.tag = validated_data.get('tag', instance.tag)
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        
        # Handle collections if provided
        collections_data = validated_data.get('collections')
        if collections_data is not None:
            # If no collections have IDs, replace all (delete old, create new)
            has_any_ids = any('id' in item for item in collections_data)
            
            if not has_any_ids:
                # Replace mode: delete all existing and create new ones
                instance.collections.all().delete()
                for collection_data in collections_data:
                    # Clean up empty image strings
                    if 'image' in collection_data and collection_data['image'] == '':
                        collection_data['image'] = ''
                    Collection.objects.create(
                        homepage_collections=instance,
                        **collection_data
                    )
            else:
                # Update/Create mode: match by ID
                existing_ids = set()
                for collection_data in collections_data:
                    collection_id = collection_data.get('id')
                    
                    # Clean up empty image strings
                    if 'image' in collection_data and collection_data['image'] == '':
                        collection_data['image'] = ''
                    
                    if collection_id:
                        # Update existing
                        Collection.objects.filter(id=collection_id, homepage_collections=instance).update(**{
                            k: v for k, v in collection_data.items() if k != 'id'
                        })
                        existing_ids.add(collection_id)
                    else:
                        # Create new
                        new_collection = Collection.objects.create(
                            homepage_collections=instance,
                            **collection_data
                        )
                        existing_ids.add(new_collection.id)
        
        instance.save()
        return instance


class HomepageCollectionsPublicSerializer(serializers.ModelSerializer):
    """Public read-only serializer for Homepage Collections."""
    
    collections = serializers.SerializerMethodField()
    
    def get_collections(self, obj):
        # For public, only active collections
        collections = obj.collections.filter(is_active=True).order_by('sort_order', 'name')
        return CollectionPublicSerializer(collections, many=True).data
    
    class Meta:
        model = HomepageCollections
        fields = [
            'tag',
            'title',
            'description',
            'collections',
        ]
