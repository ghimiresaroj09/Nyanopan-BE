import uuid

from django.db import models

from apps.common.utilities import unique_slugify


class TimeStampedModel(models.Model):
    """Abstract base model with a UUID primary key plus timestamps."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SluggedModelMixin(models.Model):
    """Keeps ``slug`` in sync with ``name``.

    - blank slug → generated from the name;
    - name changed while the slug was left untouched → slug regenerated;
    - explicitly set slug → always respected.
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        row = None
        if self.pk:
            row = type(self).objects.filter(pk=self.pk).values_list("name", "slug").first()
        if not (self.slug or "").strip():
            self.slug = unique_slugify(self, self.name)
        elif row is not None and row[0] != self.name and row[1] == self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)
