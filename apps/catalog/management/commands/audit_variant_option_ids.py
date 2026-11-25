"""Audit legacy product-value IDs against canonical attribute-value IDs.

The database stores variant options as foreign keys to ProductAttributeValue.
API option IDs should be the linked AttributeValue IDs. This command prints
that mapping and reports inconsistent/orphaned links without changing data.
"""

from django.core.management.base import BaseCommand
from apps.catalog.models import ProductVariantOption


class Command(BaseCommand):
    help = "Report legacy-to-canonical option ID mappings and invalid variant links."

    def handle(self, *args, **options):
        rows = ProductVariantOption.objects.select_related(
            "variant", "product_attribute_value", "product_attribute_value__attribute",
            "product_attribute_value__attribute_value",
        ).order_by("variant_id", "id")
        mapped = 0
        orphaned = 0
        for row in rows:
            pav = row.product_attribute_value
            problems = []
            if pav.product_id != row.variant.product_id:
                problems.append("product mismatch")
            if pav.attribute_id != pav.attribute_value.attribute_id:
                problems.append("attribute/value mismatch")
            if problems:
                orphaned += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"ORPHAN option={row.pk} variant={row.variant_id} "
                        f"product_value={pav.pk}: {', '.join(problems)}"
                    )
                )
                continue
            mapped += 1
            self.stdout.write(
                f"variant={row.variant_id} legacy_product_value_id={pav.pk} "
                f"canonical_attribute_value_id={pav.attribute_value_id} "
                f"attribute={pav.attribute.name!r} value={pav.attribute_value.name!r}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Mapped {mapped} valid variant option(s); reported {orphaned} "
                "orphaned/inconsistent reference(s). No data was changed."
            )
        )
