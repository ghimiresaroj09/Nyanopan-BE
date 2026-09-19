"""Management command to seed Our Makers page with sample data."""

from django.core.management.base import BaseCommand

from apps.cms.models import OurMakers, TeamMember


class Command(BaseCommand):
    help = "Initialize Our Makers page with sample team members"

    def handle(self, *args, **options):
        page = OurMakers.get_page()
        page.title = "Meet Our Makers"
        page.description = "Our skilled artisans blend traditional Nepali craftsmanship with modern design to create unique, comfortable footwear."
        page.save()
        
        self.stdout.write(self.style.SUCCESS(f"✓ Our Makers page: {page.title}"))
        
        # Sample team members
        sample_members = [
            {
                'name': 'Rajesh Kumar',
                'role': 'Master Craftsman',
                'intro': 'With over 20 years of experience, Rajesh leads our artisan team in creating handcrafted wool felt slippers.',
                'sort_order': 1,
            },
            {
                'name': 'Sita Devi',
                'role': 'Lead Designer',
                'intro': 'Sita brings traditional Nepali design patterns into contemporary footwear, creating unique and beautiful pieces.',
                'sort_order': 2,
            },
            {
                'name': 'Anil Sharma',
                'role': 'Quality Specialist',
                'intro': 'Anil ensures every pair of slippers meets our high standards for comfort, durability, and craftsmanship.',
                'sort_order': 3,
            },
        ]
        
        created_count = 0
        for member_data in sample_members:
            member, created = TeamMember.objects.get_or_create(
                our_makers=page,
                name=member_data['name'],
                defaults={
                    'role': member_data['role'],
                    'intro': member_data['intro'],
                    'sort_order': member_data['sort_order'],
                    'image': '',  # Will be set from admin
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"  ✓ Created: {member.name} - {member.role}")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"  ○ Already exists: {member.name}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Our Makers initialized: {created_count} new members added"
            )
        )
