from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0010_make_product_model_optional")]

    operations = [
        migrations.AddField(
            model_name="attribute",
            name="display_order",
            field=models.PositiveIntegerField(
                db_index=True,
                default=0,
                help_text="Controls the order in which this attribute is displayed.",
            ),
        ),
        migrations.AlterModelOptions(
            name="attribute",
            options={"ordering": ["display_order", "name", "id"]},
        ),
    ]
