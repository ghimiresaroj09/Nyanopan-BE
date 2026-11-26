from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0016_blog_og_url_robots_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="blog",
            name="image_title",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="blog",
            name="image_alt",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="blog",
            name="image_caption",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
    ]
