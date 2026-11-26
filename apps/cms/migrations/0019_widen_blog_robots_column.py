from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("cms", "0018_blog_image_url_capacity"),
    ]

    operations = [
        migrations.RunSQL(
            sql="ALTER TABLE cms_blog ALTER COLUMN meta_robots TYPE varchar(64)",
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
