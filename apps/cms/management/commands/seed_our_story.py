"""Management command to seed Our Story page with sample data."""

from django.core.management.base import BaseCommand

from apps.cms.models import OurStory, StorySubsection


class Command(BaseCommand):
    help = "Initialize Our Story page with sample content"

    def handle(self, *args, **options):
        page = OurStory.get_page()
        
        # Main content
        page.title = "Our Story"
        page.description = "Discover the journey of Nyanopan - from traditional craftsmanship to modern comfort."
        
        # Section 1
        page.section1_title = "Where It All Began"
        page.section1_description = "Founded in the heart of Nepal, Nyanopan started with a simple mission: to preserve traditional wool felt craftsmanship while creating comfortable, modern footwear. Our founders saw the beauty in handmade slippers and wanted to share it with the world."
        page.section1_image = ""  # Will be set from admin
        
        # Section 2
        page.section2_title = "Our Craftsmanship"
        page.section2_description = "Each pair of Nyanopan slippers is handcrafted by skilled Nepali artisans who have perfected their craft over generations. We use only the finest wool felt, sourced sustainably and processed using traditional methods that ensure durability and comfort."
        page.section2_image = ""  # Will be set from admin
        
        # Section 3
        page.section3_title = "Our Journey"
        
        page.save()
        
        self.stdout.write(self.style.SUCCESS(f"✓ Our Story page: {page.title}"))
        
        # Sample subsections for Section 3
        sample_subsections = [
            {
                'title': '2015 - The Beginning',
                'description': 'Started with a small workshop in Kathmandu with just 5 artisans, creating traditional felt slippers.',
                'sort_order': 1,
            },
            {
                'title': '2018 - Growing Our Team',
                'description': 'Expanded to 20 skilled artisans and introduced modern designs while maintaining traditional techniques.',
                'sort_order': 2,
            },
            {
                'title': '2021 - Going Global',
                'description': 'Launched our online store and started shipping worldwide, bringing Nepali craftsmanship to homes everywhere.',
                'sort_order': 3,
            },
            {
                'title': '2024 - Sustainable Future',
                'description': 'Committed to 100% sustainable materials and fair trade practices, ensuring our craft benefits both artisans and the environment.',
                'sort_order': 4,
            },
        ]
        
        created_count = 0
        for subsection_data in sample_subsections:
            subsection, created = StorySubsection.objects.get_or_create(
                our_story=page,
                title=subsection_data['title'],
                defaults={
                    'description': subsection_data['description'],
                    'sort_order': subsection_data['sort_order'],
                    'image': '',  # Will be set from admin
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Created: {subsection.title}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"  ○ Already exists: {subsection.title}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Our Story initialized: {created_count} new subsections added"
            )
        )
