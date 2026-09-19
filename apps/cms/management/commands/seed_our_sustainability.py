"""Management command to seed Our Sustainability page with sample data."""

from django.core.management.base import BaseCommand

from apps.cms.models import OurSustainability, SustainabilitySection


class Command(BaseCommand):
    help = "Initialize Our Sustainability page with sample sections"

    def handle(self, *args, **options):
        page = OurSustainability.get_page()
        
        page.title = "Our Sustainability"
        page.description = "At Nyanopan, sustainability isn't just a buzzword—it's woven into every fiber of what we do. From sourcing materials to crafting each pair of slippers, we're committed to protecting our planet and supporting our communities."
        page.save()
        
        self.stdout.write(self.style.SUCCESS(f"✓ Our Sustainability page: {page.title}"))
        
        # Sample sections
        sample_sections = [
            {
                'title': 'Sustainable Materials',
                'description': 'We use 100% natural wool felt, sourced from ethical suppliers who prioritize animal welfare. Our materials are biodegradable and renewable, ensuring minimal environmental impact.',
                'sort_order': 1,
            },
            {
                'title': 'Zero Waste Production',
                'description': 'Our production process is designed to minimize waste. Fabric scraps are repurposed into smaller products, and we continuously work to reduce our carbon footprint.',
                'sort_order': 2,
            },
            {
                'title': 'Fair Trade Practices',
                'description': 'Every artisan is paid fair wages and works in safe conditions. We believe in empowering local communities and preserving traditional craftsmanship.',
                'sort_order': 3,
            },
            {
                'title': 'Eco-Friendly Packaging',
                'description': "All our packaging is made from recycled and recyclable materials. We've eliminated plastic from our supply chain and use biodegradable alternatives.",
                'sort_order': 4,
            },
            {
                'title': 'Carbon Neutral Shipping',
                'description': 'We partner with carbon-neutral shipping providers and offset emissions from all deliveries through verified environmental projects.',
                'sort_order': 5,
            },
        ]
        
        created_count = 0
        for section_data in sample_sections:
            section, created = SustainabilitySection.objects.get_or_create(
                our_sustainability=page,
                title=section_data['title'],
                defaults={
                    'description': section_data['description'],
                    'sort_order': section_data['sort_order'],
                    'image': '',  # Will be set from admin
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Created: {section.title}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"  ○ Already exists: {section.title}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Our Sustainability initialized: {created_count} new sections added"
            )
        )
