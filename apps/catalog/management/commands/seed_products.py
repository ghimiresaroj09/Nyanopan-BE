"""Seed 20 Nyanopan products with two size variants each."""

from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.catalog.models import (
    Attribute,
    AttributeValue,
    Category,
    Product,
    ProductAttributeValue,
    ProductModel,
    ProductVariant,
)
from apps.catalog.services.variants import VariantService


PRODUCTS = [
    ("Alpine Wool Felt Slippers", "UNISEX", "LEATHER", 4200),
    ("Cloud Grey House Slippers", "WOMEN", "LEATHER", 3900),
    ("Evergreen Crepe Sole Slippers", "UNISEX", "RUBBER", 4500),
    ("Misty Morning Felt Clogs", "WOMEN", "RUBBER", 4700),
    ("Himalayan Trail House Shoes", "MEN", "RUBBER", 4900),
    ("Soft Sand Wool Loafers", "UNISEX", "LEATHER", 4300),
    ("Rose Garden Felt Slippers", "WOMEN", "LEATHER", 4100),
    ("Midnight Wool Clogs", "MEN", "RUBBER", 4800),
    ("Meadow Green Indoor Slippers", "UNISEX", "LEATHER", 4000),
    ("Warm Hearth Felt Mules", "WOMEN", "RUBBER", 4600),
    ("Kathmandu Artisan House Shoes", "UNISEX", "LEATHER", 4400),
    ("Riverstone Wool Slippers", "MEN", "LEATHER", 4300),
    ("Sunrise Felted Clogs", "WOMEN", "RUBBER", 4650),
    ("Quiet Evening Wool Mules", "UNISEX", "LEATHER", 4150),
    ("Forest Path Crepe Slippers", "MEN", "RUBBER", 4750),
    ("Snowfall Wool House Shoes", "UNISEX", "LEATHER", 4250),
    ("Poppy Red Felt Slippers", "WOMEN", "LEATHER", 4050),
    ("Stone Ridge Indoor Clogs", "MEN", "RUBBER", 4550),
    ("Little Summit Wool Slippers", "KIDS", "LEATHER", 3200),
    ("Golden Hour Felt House Shoes", "UNISEX", "RUBBER", 4450),
]


class Command(BaseCommand):
    help = "Create 20 demo products with two size variants each. Safe to rerun."

    @transaction.atomic
    def handle(self, *args, **options):
        category = Category.objects.filter(is_active=True, name__iexact="Shoes").first()
        if category is None:
            raise CommandError("An active 'Shoes' category is required.")

        size_attribute = Attribute.objects.filter(name__iexact="Size").first()
        if size_attribute is None:
            raise CommandError("A 'Size' product attribute is required.")

        sizes = list(
            AttributeValue.objects.filter(
                attribute=size_attribute, is_active=True, name__in=["36", "37"]
            ).order_by("name")
        )
        if len(sizes) != 2:
            raise CommandError("Active Size values '36' and '37' are required.")

        image_refs = list(
            Product.objects.exclude(feature_image="")
            .values_list("feature_image", flat=True)
            .distinct()
        )
        if not image_refs:
            raise CommandError("At least one existing product image is required.")

        product_model = ProductModel.objects.filter(is_active=True).first()
        created_products = 0
        created_variants = 0

        for index, (name, gender, sole_type, price) in enumerate(PRODUCTS, start=1):
            slug = slugify(name)
            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "model": product_model,
                    "gender": gender,
                    "usage_location": "BOTH",
                    "sole_type": sole_type,
                    "description": (
                        f"Hand-felted wool {name.lower()} made for comfortable everyday wear. "
                        "Choose a leather sole for quiet indoor use or a grippy crepe option "
                        "for short steps around the home."
                    ),
                    "general_information": (
                        "Made by hand in Kathmandu using wool felt and carefully finished "
                        "for a soft, comfortable fit."
                    ),
                    "materials_used": "Wool felt upper; "
                    + ("vegetable-tanned leather sole" if sole_type == "LEATHER" else "natural crepe rubber sole"),
                    "category": category,
                    "is_featured": index <= 4,
                    "is_active": True,
                    "key_features": [
                        "Hand-felted wool upper",
                        "Made in Kathmandu",
                        "Comfortable everyday indoor footwear",
                    ],
                    "feature_image": image_refs[(index - 1) % len(image_refs)],
                    "feature_image_title": name,
                    "feature_image_caption": f"Hand-felted wool footwear: {name}.",
                    "feature_image_alt": f"{name} made with a hand-felted wool upper",
                },
            )
            if created:
                created_products += 1
            elif not product.variants.exists():
                # Existing records with the same seed slug receive variants,
                # while their product content remains untouched.
                pass

            product_sizes = []
            for size in sizes:
                product_size, _ = ProductAttributeValue.objects.get_or_create(
                    product=product,
                    attribute=size_attribute,
                    attribute_value=size,
                )
                product_sizes.append((size, product_size))

            for size, product_size in product_sizes:
                sku = f"NYA-SEED-{index:02d}-{size.name}"
                if ProductVariant.objects.filter(sku=sku).exists():
                    continue
                VariantService.create_variant(
                    product=product,
                    price=Decimal(price),
                    option_pav_ids=[product_size.pk],
                    sku=sku,
                    name=f"{name} - Size {size.name}",
                )
                created_variants += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_products} products and {created_variants} variants. "
                "The 20 seed products each have two size variants."
            )
        )
