from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0009_make_gender_optional")]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="model",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.PROTECT,
                related_name="products",
                to="catalog.productmodel",
            ),
        ),
    ]
