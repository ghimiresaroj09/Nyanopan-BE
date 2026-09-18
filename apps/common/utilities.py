"""Small reusable helpers shared across apps."""

import datetime
from decimal import Decimal

from django.db import models
from django.utils.text import slugify


def unique_slugify(instance: models.Model, value: str, *, slug_field: str = "slug") -> str:
    """Return a unique slug for ``instance`` derived from ``value``.

    Appends ``-2``, ``-3`` ... until the slug is unique (excluding the
    instance itself). Respects the slug field's ``max_length``.
    """
    max_length = instance._meta.get_field(slug_field).max_length
    base = slugify(value or "") or "item"
    if max_length:
        base = base[:max_length]
    slug = base
    queryset = type(instance).objects.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    counter = 2
    while queryset.filter(**{slug_field: slug}).exists():
        suffix = f"-{counter}"
        slug = f"{base[: max_length - len(suffix)]}{suffix}" if max_length else f"{base}{suffix}"
        counter += 1
    return slug


def format_price(value: Decimal | float | str) -> str:
    """Format a price as a string with exactly two decimal places."""
    return format(Decimal(str(value)), ".2f")


def format_zulu(value: datetime.datetime) -> str:
    """Format a datetime as ``2026-09-17T10:00:00.000Z`` (UTC, millis)."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=datetime.timezone.utc)
    value = value.astimezone(datetime.timezone.utc)
    return value.strftime("%Y-%m-%dT%H:%M:%S.") + f"{value.microsecond // 1000:03d}Z"
