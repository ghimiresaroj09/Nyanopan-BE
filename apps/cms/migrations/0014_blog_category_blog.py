import uuid

from django.db import migrations, models
import django.db.models.deletion
import apps.common.storages
import apps.cms.models
import apps.common.validators


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0013_faq_category_faq"),
    ]

    operations = [
        migrations.CreateModel(
            name="BlogCategory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=150, unique=True)),
            ],
            options={
                "verbose_name": "Blog Category",
                "verbose_name_plural": "Blog Categories",
                "db_table": "cms_blog_category",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Blog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=255)),
                (
                    "image",
                    models.ImageField(
                        upload_to=apps.cms.models.blog_image_path,
                        storage=apps.common.storages.image_storage,
                        validators=[apps.common.validators.validate_image_upload],
                    ),
                ),
                ("content", models.TextField(help_text="Rich text content stored as HTML.")),
                ("tags", models.JSONField(blank=True, default=list)),
                ("is_featured", models.BooleanField(db_index=True, default=False)),
                ("is_published", models.BooleanField(db_index=True, default=False)),
                ("views", models.PositiveIntegerField(db_index=True, default=0)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="blogs",
                        to="cms.blogcategory",
                    ),
                ),
            ],
            options={
                "db_table": "cms_blog",
                "ordering": ["-created_at"],
            },
        ),
    ]
