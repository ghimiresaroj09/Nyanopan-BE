import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0012_contact_message_reply"),
    ]

    operations = [
        migrations.CreateModel(
            name="FAQCategory",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=150, unique=True)),
            ],
            options={
                "verbose_name": "FAQ Category",
                "verbose_name_plural": "FAQ Categories",
                "db_table": "cms_faq_category",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="FAQ",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("question", models.CharField(max_length=500)),
                ("answer", models.TextField()),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="faqs",
                        to="cms.faqcategory",
                    ),
                ),
            ],
            options={
                "db_table": "cms_faq",
                "ordering": ["category__name", "question"],
            },
        ),
    ]
