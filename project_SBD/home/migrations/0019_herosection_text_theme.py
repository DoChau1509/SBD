from django.db import migrations, models


def ensure_text_theme_column(apps, schema_editor):
    table_name = "home_herosection"
    connection = schema_editor.connection

    with connection.cursor() as cursor:
        existing_tables = connection.introspection.table_names(cursor)
        if table_name not in existing_tables:
            return

        columns = {
            column.name
            for column in connection.introspection.get_table_description(cursor, table_name)
        }
        if "text_theme" in columns:
            return

        quote_name = schema_editor.quote_name
        cursor.execute(
            f"ALTER TABLE {quote_name(table_name)} "
            "ADD COLUMN text_theme varchar(10) NOT NULL DEFAULT 'light'"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0018_homewhychoosesection_homewhychooseitem"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql="""
                    CREATE TABLE IF NOT EXISTS home_herosection (
                        id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                        badge_text varchar(200) NOT NULL,
                        heading_line1 varchar(300) NOT NULL,
                        heading_line2 varchar(300) NOT NULL,
                        description text NOT NULL,
                        btn_primary_text varchar(100) NOT NULL,
                        btn_primary_url varchar(200) NOT NULL,
                        btn_outline_text varchar(100) NOT NULL,
                        btn_outline_url varchar(200) NOT NULL,
                        stat_1_num varchar(20) NOT NULL,
                        stat_1_label varchar(100) NOT NULL,
                        stat_2_num varchar(20) NOT NULL,
                        stat_2_label varchar(100) NOT NULL,
                        stat_3_num varchar(20) NOT NULL,
                        stat_3_label varchar(100) NOT NULL,
                        stat_4_num varchar(20) NOT NULL,
                        stat_4_label varchar(100) NOT NULL,
                        bg_type varchar(20) NOT NULL,
                        bg_image varchar(100) NULL,
                        bg_video varchar(100) NULL,
                        text_theme varchar(10) NOT NULL DEFAULT 'light',
                        is_active bool NOT NULL,
                        updated_at datetime NOT NULL
                    )
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    sql="""
                    CREATE TABLE IF NOT EXISTS home_herocarouselimage (
                        id integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                        image varchar(100) NOT NULL,
                        "order" integer unsigned NOT NULL,
                        hero_id bigint NOT NULL REFERENCES home_herosection (id)
                            DEFERRABLE INITIALLY DEFERRED
                    )
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunSQL(
                    sql="""
                    CREATE INDEX IF NOT EXISTS home_herocarouselimage_hero_id_idx
                    ON home_herocarouselimage (hero_id)
                    """,
                    reverse_sql=migrations.RunSQL.noop,
                ),
                migrations.RunPython(ensure_text_theme_column, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.CreateModel(
                    name="HeroSection",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("badge_text", models.CharField(max_length=200, verbose_name="Badge text (vd: Hơn 15 năm...)")),
                        ("heading_line1", models.CharField(max_length=300, verbose_name="Tiêu đề dòng 1")),
                        ("heading_line2", models.CharField(blank=True, max_length=300, verbose_name="Tiêu đề dòng 2 (vàng)")),
                        ("description", models.TextField(verbose_name="Mô tả")),
                        ("btn_primary_text", models.CharField(default="Giới Thiệu", max_length=100, verbose_name="Nút chính - text")),
                        ("btn_primary_url", models.CharField(default="/about/", max_length=200, verbose_name="Nút chính - URL")),
                        ("btn_outline_text", models.CharField(default="Xem Dự Án", max_length=100, verbose_name="Nút phụ - text")),
                        ("btn_outline_url", models.CharField(default="/project/", max_length=200, verbose_name="Nút phụ - URL")),
                        ("stat_1_num", models.CharField(default="500+", max_length=20)),
                        ("stat_1_label", models.CharField(default="Dự án hoàn thành", max_length=100)),
                        ("stat_2_num", models.CharField(default="15+", max_length=20)),
                        ("stat_2_label", models.CharField(default="Năm kinh nghiệm", max_length=100)),
                        ("stat_3_num", models.CharField(default="200+", max_length=20)),
                        ("stat_3_label", models.CharField(default="Kỹ sư & Chuyên gia", max_length=100)),
                        ("stat_4_num", models.CharField(default="98%", max_length=20)),
                        ("stat_4_label", models.CharField(default="Khách hàng hài lòng", max_length=100)),
                        ("bg_type", models.CharField(choices=[("color", "Màu nền (mặc định)"), ("image", "Ảnh nền"), ("video", "Video tự chạy"), ("carousel", "Carousel nhiều ảnh")], default="color", max_length=20, verbose_name="Loại nền")),
                        ("bg_image", models.ImageField(blank=True, null=True, upload_to="hero/", verbose_name="Ảnh nền")),
                        ("bg_video", models.FileField(blank=True, null=True, upload_to="hero/videos/", verbose_name="Video nền (mp4)")),
                        ("text_theme", models.CharField(choices=[("light", "Chữ sáng"), ("dark", "Chữ tối")], default="light", max_length=10, verbose_name="Theme màu chữ")),
                        ("is_active", models.BooleanField(default=True)),
                        ("updated_at", models.DateTimeField(auto_now=True)),
                    ],
                    options={"verbose_name": "Hero Section"},
                ),
                migrations.CreateModel(
                    name="HeroCarouselImage",
                    fields=[
                        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                        ("image", models.ImageField(upload_to="hero/carousel/", verbose_name="Ảnh")),
                        ("order", models.PositiveIntegerField(default=0)),
                        ("hero", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="carousel_images", to="home.herosection")),
                    ],
                    options={"ordering": ["order"]},
                ),
            ],
        ),
    ]
