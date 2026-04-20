from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0019_herosection_text_theme"),
    ]

    operations = [
        migrations.CreateModel(
            name="AboutVideoTour",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("section_title", models.CharField(default="Quy Trình Triển Khai Dự Án", max_length=255, verbose_name="Tiêu đề khối")),
                ("section_description", models.TextField(default="Minh bạch từng bước — kiểm soát chất lượng và tiến độ theo tiêu chuẩn", verbose_name="Mô tả khối")),
                ("step_1_icon", models.CharField(default="fa fa-search", max_length=100, verbose_name="Icon bước 1")),
                ("step_1_title", models.CharField(default="Khảo sát", max_length=150, verbose_name="Tiêu đề bước 1")),
                ("step_1_description", models.TextField(default="Tiếp nhận nhu cầu, khảo sát hiện trạng và tư vấn phương án tối ưu.", verbose_name="Mô tả bước 1")),
                ("step_2_icon", models.CharField(default="fa-solid fa-file-lines", max_length=100, verbose_name="Icon bước 2")),
                ("step_2_title", models.CharField(default="Báo giá", max_length=150, verbose_name="Tiêu đề bước 2")),
                ("step_2_description", models.TextField(default="Lập hồ sơ kỹ thuật, dự toán chi tiết và thống nhất hợp đồng.", verbose_name="Mô tả bước 2")),
                ("step_3_icon", models.CharField(default="fa fa-gavel", max_length=100, verbose_name="Icon bước 3")),
                ("step_3_title", models.CharField(default="Thi công", max_length=150, verbose_name="Tiêu đề bước 3")),
                ("step_3_description", models.TextField(default="Triển khai theo tiến độ, nghiệm thu theo giai đoạn và bàn giao.", verbose_name="Mô tả bước 3")),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Video tour trang giới thiệu",
            },
        ),
    ]
