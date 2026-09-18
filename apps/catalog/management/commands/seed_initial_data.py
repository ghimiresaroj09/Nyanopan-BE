"""Seed extensible catalog primitives: base attributes.

Idempotent: safe to run multiple times.
"""

from django.core.management.base import BaseCommand

from apps.catalog.models import Attribute


class Command(BaseCommand):
    help = "Seed initial attributes (Color/Size/Material)."

    def handle(self, *args, **options):
        attributes = [
            ("Color", True),
            ("Size", False),
            ("Material", False),
        ]
        for name, requires_image in attributes:
            attribute, created = Attribute.objects.get_or_create(
                name=name, defaults={"requires_image": requires_image}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created attribute: {name}"))
            elif attribute.requires_image != requires_image:
                attribute.requires_image = requires_image
                attribute.save(update_fields=["requires_image"])
                self.stdout.write(f"Updated attribute: {name}")
            else:
                self.stdout.write(f"Attribute already exists: {name}")
