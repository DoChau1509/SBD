from django.db import migrations, models
import django.db.models.deletion
from django.utils.text import slugify


DEFAULT_CORE_VALUES_CONTENT = (
    "Chính trực — Chuyên nghiệp — Sáng tạo — Bền vững. "
    "Chúng tôi xây không chỉ những tòa nhà, mà còn xây dựng lòng tin "
    "và các mối quan hệ đối tác lâu dài."
)


def forwards_create_types_and_map_statements(apps, schema_editor):
    AboutStatement = apps.get_model("home", "AboutStatement")
    AboutStatementType = apps.get_model("home", "AboutStatementType")

    default_types = [
        ("Tầm nhìn", 1),
        ("Sứ mệnh", 2),
        ("Giá trị cốt lõi", 3),
    ]

    created_types = {}
    for name, order in default_types:
        obj, _ = AboutStatementType.objects.get_or_create(
            name=name,
            defaults={
                "slug": slugify(name) or f"loai-{order}",
                "order": order,
                "is_active": True,
            },
        )
        created_types[name] = obj

    mapping = {
        "vision": created_types["Tầm nhìn"],
        "mission": created_types["Sứ mệnh"],
    }

    for statement in AboutStatement.objects.all():
        target_type = mapping.get(statement.statement_type)
        if target_type:
            statement.statement_type_fk_id = target_type.id
            statement.save(update_fields=["statement_type_fk"])


def forwards_create_core_values_statement(apps, schema_editor):
    AboutStatement = apps.get_model("home", "AboutStatement")
    AboutStatementType = apps.get_model("home", "AboutStatementType")

    core_type, _ = AboutStatementType.objects.get_or_create(
        name="Giá trị cốt lõi",
        defaults={
            "slug": slugify("Giá trị cốt lõi") or "gia-tri-cot-loi",
            "order": 3,
            "is_active": True,
        },
    )

    exists = AboutStatement.objects.filter(statement_type=core_type).exists()
    if not exists:
        AboutStatement.objects.create(
            title="Giá Trị Cốt Lõi",
            statement_type=core_type,
            content=DEFAULT_CORE_VALUES_CONTENT,
            icon="fa-heart",
            order=0,
            is_active=True,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0013_project_is_featured"),
    ]

    operations = [
        migrations.CreateModel(
            name="AboutStatementType",
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
                    "name",
                    models.CharField(
                        max_length=100, unique=True, verbose_name="Tên loại"
                    ),
                ),
                ("slug", models.SlugField(blank=True, max_length=120, unique=True)),
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
            options={
                "verbose_name": "Loại tầm nhìn / sứ mệnh",
                "verbose_name_plural": "Loại tầm nhìn / sứ mệnh",
                "ordering": ["order", "created_at", "name"],
            },
        ),
        migrations.AddField(
            model_name="aboutstatement",
            name="statement_type_fk",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="temp_statements",
                to="home.aboutstatementtype",
                verbose_name="Loại nội dung",
            ),
        ),
        migrations.RunPython(
            forwards_create_types_and_map_statements,
            migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name="aboutstatement",
            name="statement_type",
        ),
        migrations.RenameField(
            model_name="aboutstatement",
            old_name="statement_type_fk",
            new_name="statement_type",
        ),
        migrations.AlterModelOptions(
            name="aboutstatement",
            options={
                "ordering": ["order", "created_at"],
                "verbose_name": "Nội dung tầm nhìn / sứ mệnh",
                "verbose_name_plural": "Nội dung tầm nhìn / sứ mệnh",
            },
        ),
        migrations.AlterField(
            model_name="aboutstatement",
            name="title",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Có thể để trống để dùng tên loại nội dung.",
                max_length=150,
                verbose_name="Tiêu đề",
            ),
        ),
        migrations.AlterField(
            model_name="aboutstatement",
            name="icon",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Có thể nhập fa-eye, fa-solid fa-eye, cart-arrow-down hoặc URL icon từ Font Awesome.",
                max_length=500,
                verbose_name="Icon Font Awesome / Icon URL",
            ),
        ),
        migrations.AlterField(
            model_name="aboutstatement",
            name="statement_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="statements",
                to="home.aboutstatementtype",
                verbose_name="Loại nội dung",
            ),
        ),
        migrations.RunPython(
            forwards_create_core_values_statement,
            migrations.RunPython.noop,
        ),
    ]
