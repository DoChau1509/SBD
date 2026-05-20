from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0025_sitebrandsettings_footer_bottom_text"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitebrandsettings",
            name="preloader_image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="branding/preloader/",
                verbose_name="Ảnh màn hình loading",
            ),
        ),
    ]
