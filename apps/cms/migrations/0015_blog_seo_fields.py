from django.db import migrations, models
from django.utils.text import slugify
import apps.common.storages
import apps.cms.models
import apps.common.validators


def populate_blog_slugs(apps, schema_editor):
    Blog = apps.get_model("cms", "Blog")
    database = schema_editor.connection.alias
    for blog in Blog.objects.using(database).all().only("pk", "title").iterator():
        base = slugify(blog.title) or f"blog-{str(blog.pk)[:8]}"
        candidate = base[:255]
        suffix = 2
        while Blog.objects.using(database).filter(slug=candidate).exclude(pk=blog.pk).exists():
            ending = f"-{suffix}"
            candidate = f"{base[:255 - len(ending)]}{ending}"
            suffix += 1
        Blog.objects.using(database).filter(pk=blog.pk).update(slug=candidate)


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0014_blog_category_blog"),
    ]

    operations = [
        migrations.AddField(
            model_name="blog",
            name="slug",
            field=models.SlugField(blank=True, db_index=False, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name="blog",
            name="excerpt",
            field=models.CharField(blank=True, default="", max_length=500),
        ),
        migrations.AddField(
            model_name="blog",
            name="meta_title",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="blog",
            name="meta_description",
            field=models.CharField(blank=True, default="", max_length=320),
        ),
        migrations.AddField(
            model_name="blog",
            name="meta_keywords",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="blog",
            name="canonical_url",
            field=models.URLField(blank=True, default="", max_length=500),
        ),
        migrations.AddField(
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
        migrations.AddField(
            model_name="blog",
            name="og_title",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="blog",
            name="og_description",
            field=models.CharField(blank=True, default="", max_length=320),
        ),
        migrations.AddField(
            model_name="blog",
            name="og_image",
            field=models.ImageField(
                blank=True,
                upload_to=apps.cms.models.blog_image_path,
                storage=apps.common.storages.image_storage,
                validators=[apps.common.validators.validate_image_upload],
            ),
        ),
        migrations.AddField(
            model_name="blog",
            name="twitter_card",
            field=models.CharField(
                choices=[("summary", "Summary"), ("summary_large_image", "Summary with large image")],
                default="summary_large_image",
                max_length=32,
            ),
        ),
        migrations.AddField(
            model_name="blog",
            name="twitter_title",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="blog",
            name="twitter_description",
            field=models.CharField(blank=True, default="", max_length=320),
        ),
        migrations.AddField(
            model_name="blog",
            name="twitter_image",
            field=models.ImageField(
                blank=True,
                upload_to=apps.cms.models.blog_image_path,
                storage=apps.common.storages.image_storage,
                validators=[apps.common.validators.validate_image_upload],
            ),
        ),
        migrations.RunPython(populate_blog_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="blog",
            name="slug",
            field=models.SlugField(blank=True, db_index=False, max_length=255, unique=True),
        ),
    ]
