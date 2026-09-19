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
        for field in ['email', 'phone', 'whatsapp', 'address', 'map_url']:
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
