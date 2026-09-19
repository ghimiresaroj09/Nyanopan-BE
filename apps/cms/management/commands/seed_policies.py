"""Management command to seed initial policies."""

from django.core.management.base import BaseCommand

from apps.cms.models import Policy, PolicyType


class Command(BaseCommand):
    help = "Initialize policies with default content"

    def handle(self, *args, **options):
        policies_data = [
            {
                'type': PolicyType.SHIPPING,
                'title': 'Shipping Policy',
                'content': '<h2>Shipping Policy</h2><p>We ship within 3-5 business days. Free shipping on orders over $50.</p>',
            },
            {
                'type': PolicyType.EXCHANGES_RETURNS,
                'title': 'Exchanges & Returns',
                'content': '<h2>Exchanges & Returns</h2><p>30-day return policy. Items must be in original condition.</p>',
            },
            {
                'type': PolicyType.PRIVACY_POLICY,
                'title': 'Privacy Policy',
                'content': '<h2>Privacy Policy</h2><p>We respect your privacy and protect your personal information.</p>',
            },
            {
                'type': PolicyType.TERMS_CONDITIONS,
                'title': 'Terms and Conditions',
                'content': '<h2>Terms and Conditions</h2><p>By using our website, you agree to these terms and conditions.</p>',
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for policy_data in policies_data:
            policy, created = Policy.objects.update_or_create(
                type=policy_data['type'],
                defaults={
                    'title': policy_data['title'],
                    'content': policy_data['content'],
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Created policy: {policy.get_type_display()}")
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f"○ Policy already exists: {policy.get_type_display()}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\n✓ Policies initialized: {created_count} created, {updated_count} already existed"
            )
        )
