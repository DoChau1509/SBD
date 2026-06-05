from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0027_specializedservicecontent"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitebrandsettings",
            name="favicon_image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="branding/favicon/",
                verbose_name="Ảnh icon trình duyệt",
            ),
        ),
    ]
