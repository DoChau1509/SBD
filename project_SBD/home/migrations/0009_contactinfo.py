from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0008_certificate_image_alter_certificate_icon"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContactInfo",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "branch_name",
                    models.CharField(
                        max_length=150, verbose_name="Tên chi nhánh / văn phòng"
                    ),
                ),
                ("address", models.TextField(verbose_name="Địa chỉ")),
                (
                    "phone",
                    models.CharField(max_length=50, verbose_name="Số điện thoại"),
                ),
                (
                    "fax",
                    models.CharField(blank=True, max_length=50, verbose_name="Fax"),
                ),
                (
                    "email",
                    models.EmailField(blank=True, max_length=254, verbose_name="Email"),
                ),
                (
                    "working_hours",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="Giờ làm việc"
                    ),
                ),
                (
                    "map_embed_url",
                    models.URLField(blank=True, verbose_name="Link Google Maps Embed"),
                ),
                (
                    "facebook_url",
                    models.URLField(blank=True, verbose_name="Facebook URL"),
                ),
                (
                    "youtube_url",
                    models.URLField(blank=True, verbose_name="YouTube URL"),
                ),
                (
                    "linkedin_url",
                    models.URLField(blank=True, verbose_name="LinkedIn URL"),
                ),
                (
                    "instagram_url",
                    models.URLField(blank=True, verbose_name="Instagram URL"),
                ),
                (
                    "order",
                    models.PositiveIntegerField(
                        default=0, verbose_name="Thứ tự hiển thị"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Hiển thị"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["order", "created_at"]},
        ),
    ]
