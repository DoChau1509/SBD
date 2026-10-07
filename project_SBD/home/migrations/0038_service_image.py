from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("home", "0037_servicepage"),
    ]

    operations = [
        migrations.AddField(
            model_name="service",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="services/images/",
                verbose_name="Ảnh đại diện",
            ),
        ),
    ]
