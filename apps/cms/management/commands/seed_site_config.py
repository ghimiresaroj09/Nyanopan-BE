"""Management command to seed initial site configuration."""

from django.core.management.base import BaseCommand

from apps.cms.models import SiteConfiguration


class Command(BaseCommand):
    help = "Initialize site configuration with default values"

    def handle(self, *args, **options):
        config = SiteConfiguration.get_config()
        
        # Only set defaults if config is empty
        if not config.email:
            config.email = "contact@example.com"
            config.phone = "+977-1234567890"
            config.whatsapp = "+977-1234567890"
            config.address = "Your Business Address"
            config.map_url = "https://maps.google.com/"
            config.facebook_url = "https://facebook.com/yourpage"
            config.instagram_url = "https://instagram.com/yourpage"
            config.tiktok_url = "https://tiktok.com/@yourpage"
            config.pinterest_url = "https://pinterest.com/yourpage"
            config.save()
            
            self.stdout.write(
                self.style.SUCCESS("✓ Site configuration initialized with default values")
            )
        else:
            self.stdout.write(
                self.style.WARNING("Site configuration already exists. Skipping initialization.")
            )
