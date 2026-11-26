from django.db import migrations, models
import apps.common.storages
import apps.cms.models
import apps.common.validators


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0017_blog_image_metadata"),
    ]

    operations = [
        migrations.AlterField(
            model_name="blog",
            name="image",
            field=models.ImageField(
                max_length=500,
                upload_to=apps.cms.models.blog_image_path,
                storage=apps.common.storages.image_storage,
                validators=[apps.common.validators.validate_image_upload],
            ),
        ),
        migrations.AlterField(
            model_name="blog",
            name="og_image",
            field=models.ImageField(
                blank=True,
                max_length=500,
                upload_to=apps.cms.models.blog_image_path,
                storage=apps.common.storages.image_storage,
                validators=[apps.common.validators.validate_image_upload],
            ),
        ),
        migrations.AlterField(
            model_name="blog",
            name="twitter_image",
            field=models.ImageField(
                blank=True,
                max_length=500,
                upload_to=apps.cms.models.blog_image_path,
                storage=apps.common.storages.image_storage,
                validators=[apps.common.validators.validate_image_upload],
            ),
        ),
    ]
