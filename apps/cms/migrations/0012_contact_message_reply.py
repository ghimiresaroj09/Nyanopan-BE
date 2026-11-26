import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("cms", "0011_add_contact_message_model"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactMessageReply",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("reply", models.TextField()),
                ("subject", models.CharField(max_length=255)),
                ("sent_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "contact_message",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="replies",
                        to="cms.contactmessage",
                    ),
                ),
                (
                    "sent_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="contact_message_replies",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "cms_contact_message_reply",
                "ordering": ["sent_at", "id"],
            },
        ),
    ]
