from django.db import migrations, models


def normalize_robots_values(apps, schema_editor):
    Blog = apps.get_model("cms", "Blog")
    database = schema_editor.connection.alias
    updates = {
        "index,follow": "index, follow",
        "noindex,follow": "noindex, follow",
        "noindex,nofollow": "noindex, nofollow",
    }
    for old_value, new_value in updates.items():
        Blog.objects.using(database).filter(meta_robots=old_value).update(
            meta_robots=new_value
        )


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0015_blog_seo_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="blog",
            name="og_url",
            field=models.URLField(blank=True, default="", max_length=500),
        ),
        migrations.RunPython(normalize_robots_values, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="blog",
            name="meta_robots",
            field=models.CharField(
                choices=[
                    ("index, follow", "index, follow"),
                    ("noindex, follow", "noindex, follow"),
                    ("index, nofollow", "index, nofollow"),
                    ("noindex, nofollow", "noindex, nofollow"),
                    ("max-image-preview:large", "max-image-preview:large"),
                    ("index, follow, max-image-preview:large", "index, follow, max-image-preview:large"),
                    ("noindex, follow, max-image-preview:large", "noindex, follow, max-image-preview:large"),
                    ("index, nofollow, max-image-preview:large", "index, nofollow, max-image-preview:large"),
                    ("noindex, nofollow, max-image-preview:large", "noindex, nofollow, max-image-preview:large"),
                ],
                default="index, follow, max-image-preview:large",
                max_length=64,
            ),
        ),
    ]
