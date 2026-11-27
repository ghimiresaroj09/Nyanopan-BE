from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0018_blog_image_url_capacity"),
    ]

    # meta_robots is already max_length=64 in migration 0015 and remains so
    # through 0018. Keep this migration node for databases that have recorded
    # it, but do not issue backend-specific SQL for a redundant schema change.
    operations = []
