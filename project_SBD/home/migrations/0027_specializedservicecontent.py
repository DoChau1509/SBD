from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0026_sitebrandsettings_preloader_image"),
    ]

    operations = [
        migrations.CreateModel(
            name="SpecializedServiceContent",
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
                    "sector",
                    models.CharField(
                        choices=[
                            ("industrial", "Công nghiệp"),
                            ("civil", "Dân dụng"),
                            (
                                "energy_green",
                                "Năng lượng và công trình xanh",
                            ),
                            (
                                "interior_commercial",
                                "Nội thất và thương mại",
                            ),
                        ],
                        db_index=True,
                        max_length=30,
                        verbose_name="Lĩnh vực",
                    ),
                ),
                (
                    "title",
                    models.CharField(max_length=200, verbose_name="Tiêu đề"),
                ),
                (
                    "summary",
                    models.TextField(blank=True, verbose_name="Mô tả ngắn"),
                ),
                (
                    "content",
                    models.TextField(verbose_name="Nội dung chi tiết"),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="specialized_services/",
                        verbose_name="Ảnh minh họa",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Nội dung dịch vụ chuyên ngành",
                "verbose_name_plural": "Nội dung dịch vụ chuyên ngành",
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
