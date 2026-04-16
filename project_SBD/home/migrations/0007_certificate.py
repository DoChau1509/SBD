from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0006_aboutstatement"),
    ]

    operations = [
        migrations.CreateModel(
            name="Certificate",
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
                ("title", models.CharField(max_length=300, verbose_name="Tiêu đề")),
                ("description", models.TextField(verbose_name="Mô tả")),
                (
                    "icon",
                    models.CharField(
                        default="fa-certificate", max_length=50, verbose_name="Icon"
                    ),
                ),
                (
                    "side",
                    models.CharField(
                        choices=[("left", "Trái"), ("right", "Phải")],
                        default="left",
                        max_length=10,
                        verbose_name="Cột",
                    ),
                ),
                (
                    "order",
                    models.PositiveIntegerField(default=0, verbose_name="Thứ tự"),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Hiển thị"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["side", "order", "created_at"]},
        ),
    ]
