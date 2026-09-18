"""SKU generation.

Variant SKUs auto-generate from the product name + option values
(e.g. ``CELSI-GREY-40``) whenever the admin leaves ``sku`` blank. Explicit
SKUs are still accepted and always respected. Generation happens once at
creation; later option/name edits never rewrite an existing SKU.
"""

import re
import uuid

from django.utils.text import slugify

from ..models import ProductVariant

MAX_SKU_LENGTH = 100


def _sku_part(text: str, *, max_length: int, fallback: str) -> str:
    slug = slugify(text or "")
    part = re.sub(r"[^a-z0-9]+", "-", slug).strip("-").upper()
    part = part[:max_length].strip("-")
    return part or fallback


def _unique_sku(base: str) -> str:
    base = base[:MAX_SKU_LENGTH].strip("-") or "ITEM"
    candidate, counter = base, 2
    while ProductVariant.objects.filter(sku=candidate).exists():
        suffix = f"-{counter}"
        candidate = f"{base[: MAX_SKU_LENGTH - len(suffix)].strip('-')}{suffix}"
        counter += 1
    return candidate


def generate_sku(product, pavs) -> str:
    """Build a deterministic unique SKU from the product + option values.

    Option parts are ordered by (attribute, value) name so the SKU does not
    depend on the input order of the options.
    """
    words = (product.name or "").split()
    product_part = _sku_part(words[0] if words else "", max_length=16, fallback="ITEM")
    ordered = sorted(pavs, key=lambda pav: (pav.attribute.name, pav.attribute_value.name))
    option_parts = [
        _sku_part(pav.attribute_value.name, max_length=24, fallback="X") for pav in ordered
    ]
    return _unique_sku("-".join([product_part, *option_parts]))


def generate_fallback_sku() -> str:
    """Random unique SKU (``VAR-XXXXXXXX``) used when options are unknown,
    e.g. variants created directly in the Django admin or shell."""
    return _unique_sku(f"VAR-{uuid.uuid4().hex[:8].upper()}")
