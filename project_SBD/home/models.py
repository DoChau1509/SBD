from django.db import models
from urllib.parse import quote_plus, urlparse, parse_qs
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone


class ProjectCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(blank=True, null=True, unique=True)
    is_hidden = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class ProductCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(blank=True, null=True, unique=True)
    is_hidden = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class ManagedMediaCleanupModel(models.Model):
    managed_file_fields = ()

    class Meta:
        abstract = True

    @classmethod
    def _delete_file_if_unused(cls, field_name, file_name):
        if not file_name:
            return

        if cls.objects.filter(**{field_name: file_name}).exists():
            return

        field = cls._meta.get_field(field_name)
        field.storage.delete(file_name)

    def save(self, *args, **kwargs):
        files_to_delete = []

        if self.pk:
            old_instance = type(self).objects.filter(pk=self.pk).first()
            if old_instance:
                for field_name in self.managed_file_fields:
                    old_file = getattr(old_instance, field_name, None)
                    new_file = getattr(self, field_name, None)
                    old_name = getattr(old_file, "name", None)
                    new_name = getattr(new_file, "name", None)

                    if old_name and old_name != new_name:
                        files_to_delete.append((field_name, old_name))

        super().save(*args, **kwargs)

        for field_name, file_name in files_to_delete:
            self._delete_file_if_unused(field_name, file_name)

    def delete(self, *args, **kwargs):
        files_to_delete = [
            (field_name, getattr(getattr(self, field_name, None), "name", None))
            for field_name in self.managed_file_fields
        ]

        result = super().delete(*args, **kwargs)

        for field_name, file_name in files_to_delete:
            self._delete_file_if_unused(field_name, file_name)

        return result


class Project(ManagedMediaCleanupModel):
    managed_file_fields = ("image",)

    name = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to="projects/")
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(
        ProjectCategory,
        on_delete=models.PROTECT,
        related_name="projects",
    )
    is_featured = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Product(ManagedMediaCleanupModel):
    managed_file_fields = ("image",)

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)

    supplier_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="Tên nhà cung cấp / công ty",
    )
    supplier_address = models.TextField(
        blank=True,
        default="",
        verbose_name="Địa chỉ nhà cung cấp / công ty",
    )
    supplier_map_embed_url = models.URLField(
        blank=True,
        verbose_name="Link Google Maps của nhà cung cấp / công ty",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name="products",
    )

    @property
    def created_at_vn(self):
        if not self.created_at:
            return ""
        return timezone.localtime(self.created_at).strftime("%d/%m/%Y %H:%M")

    @property
    def created_date_vn(self):
        if not self.created_at:
            return ""
        return timezone.localtime(self.created_at).strftime("%d/%m/%Y")

    @property
    def map_display_url(self):
        raw_url = (self.supplier_map_embed_url or "").strip()
        if raw_url and ("/maps/embed" in raw_url or "output=embed" in raw_url):
            return raw_url

        query = (self.supplier_address or "").strip()
        if not query:
            return ""

        return (
            "https://maps.google.com/maps?"
            f"q={quote_plus(query)}&t=&z=15&ie=UTF8&iwloc=&output=embed"
        )

    def __str__(self):
        return self.name


# 11/4/2026: Hoàng
class PostCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(blank=True, null=True, unique=True)
    is_hidden = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Post(ManagedMediaCleanupModel):
    managed_file_fields = ("image",)

    title = models.CharField(max_length=200)
    summary = models.TextField(blank=True)
    content = models.TextField()
    image = models.ImageField(upload_to="posts/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(
        PostCategory,
        on_delete=models.PROTECT,
        related_name="posts",
    )

    def __str__(self):
        return self.title


class FAQ(models.Model):
    question = models.CharField(max_length=500, verbose_name="Câu hỏi")
    answer = models.TextField(verbose_name="Câu trả lời")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.question


###### Trịnh gia đạt làm phần dữ liệu, thêm xóa sửa phần ban lãnh đạo trong trang giới thiệu
class LeadershipMember(ManagedMediaCleanupModel):
    managed_file_fields = ("image",)

    full_name = models.CharField(max_length=150, verbose_name="Họ và tên")
    role = models.CharField(max_length=150, verbose_name="Chức vụ")
    bio = models.TextField(verbose_name="Mô tả ngắn")
    image = models.ImageField(
        upload_to="leadership/", blank=True, null=True, verbose_name="Ảnh"
    )
    initials = models.CharField(max_length=10, blank=True, verbose_name="Chữ viết tắt")
    linkedin_url = models.URLField(blank=True, verbose_name="LinkedIn URL")
    facebook_url = models.URLField(blank=True, verbose_name="Facebook URL")
    instagram_url = models.URLField(blank=True, verbose_name="Instagram URL")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự hiển thị")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.full_name


class AboutIntro(models.Model):
    # Cột trái (card tối)
    kicker = models.CharField(
        max_length=100, default="Thành lập 2009", verbose_name="Dòng nhỏ trên cùng"
    )
    brand_name = models.CharField(
        max_length=200, default="Sao Bắc Đẩu", verbose_name="Tên thương hiệu"
    )
    slogan = models.CharField(
        max_length=300, default="Chất lượng — Uy tín — Bền vững", verbose_name="Slogan"
    )
    highlight_1 = models.CharField(
        max_length=100, blank=True, verbose_name="Highlight 1 (vd: ISO 9001:2015)"
    )
    highlight_2 = models.CharField(
        max_length=100, blank=True, verbose_name="Highlight 2 (vd: 200+ kỹ sư)"
    )
    highlight_3 = models.CharField(
        max_length=100, blank=True, verbose_name="Highlight 3 (vd: Thi công toàn quốc)"
    )
    badge_number = models.CharField(
        max_length=20, default="500+", verbose_name="Số badge (vd: 500+)"
    )
    badge_text = models.CharField(
        max_length=100, default="Dự Án Hoàn Thành", verbose_name="Chữ dưới badge"
    )

    # Cột phải (text)
    heading = models.CharField(
        max_length=300,
        default="Công Ty Xây Dựng Sao Bắc Đẩu",
        verbose_name="Tiêu đề lớn",
    )
    paragraph_1 = models.TextField(verbose_name="Đoạn văn 1")
    paragraph_2 = models.TextField(blank=True, verbose_name="Đoạn văn 2")

    # Danh sách bullet (mỗi dòng 1 item)
    bullet_points = models.TextField(
        verbose_name="Danh sách điểm mạnh",
        help_text="Mỗi dòng là một bullet. VD: Chứng nhận ISO 9001:2015",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Giới thiệu công ty"

    def __str__(self):
        return self.heading

    def get_bullets(self):
        """Trả về list các bullet, bỏ dòng trống"""
        return [
            line.strip() for line in self.bullet_points.splitlines() if line.strip()
        ]


class AboutVideoTour(models.Model):
    section_title = models.CharField(
        max_length=255,
        default="Quy Trình Triển Khai Dự Án",
        verbose_name="Tiêu đề khối",
    )
    section_description = models.TextField(
        default="Minh bạch từng bước — kiểm soát chất lượng và tiến độ theo tiêu chuẩn",
        verbose_name="Mô tả khối",
    )

    step_1_icon = models.CharField(
        max_length=100, default="fa fa-search", verbose_name="Icon bước 1"
    )
    step_1_title = models.CharField(
        max_length=150, default="Khảo sát", verbose_name="Tiêu đề bước 1"
    )
    step_1_description = models.TextField(
        default="Tiếp nhận nhu cầu, khảo sát hiện trạng và tư vấn phương án tối ưu.",
        verbose_name="Mô tả bước 1",
    )

    step_2_icon = models.CharField(
        max_length=100,
        default="fa-solid fa-file-lines",
        verbose_name="Icon bước 2",
    )
    step_2_title = models.CharField(
        max_length=150, default="Báo giá", verbose_name="Tiêu đề bước 2"
    )
    step_2_description = models.TextField(
        default="Lập hồ sơ kỹ thuật, dự toán chi tiết và thống nhất hợp đồng.",
        verbose_name="Mô tả bước 2",
    )

    step_3_icon = models.CharField(
        max_length=100, default="fa fa-gavel", verbose_name="Icon bước 3"
    )
    step_3_title = models.CharField(
        max_length=150, default="Thi công", verbose_name="Tiêu đề bước 3"
    )
    step_3_description = models.TextField(
        default="Triển khai theo tiến độ, nghiệm thu theo giai đoạn và bàn giao.",
        verbose_name="Mô tả bước 3",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Video tour trang giới thiệu"

    def __str__(self):
        return self.section_title


# =========HomeWhyChooseSection
class HomeWhyChooseSection(models.Model):
    section_title = models.CharField(
        max_length=255,
        default="Tại Sao Chọn Sao Bắc Đẩu?",
        verbose_name="Tiêu đề khối bên trái",
    )
    right_kicker = models.CharField(
        max_length=100,
        default="SBD Construction",
        verbose_name="Dòng nhỏ bên phải",
    )
    right_title = models.CharField(
        max_length=255,
        default="Thi công trọn gói",
        verbose_name="Tiêu đề lớn bên phải",
    )
    right_subtitle = models.CharField(
        max_length=255,
        default="Dân dụng • Công nghiệp • Hạ tầng",
        verbose_name="Dòng mô tả bên phải",
    )
    badge_number = models.CharField(
        max_length=20,
        default="15+",
        verbose_name="Số badge",
    )
    badge_label = models.CharField(
        max_length=100,
        default="Năm Kinh Nghiệm",
        verbose_name="Chữ dưới badge",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Khối Tại Sao Chọn Chúng Tôi"
        verbose_name_plural = "Khối Tại Sao Chọn Chúng Tôi"

    def __str__(self):
        return self.section_title


class HomeWhyChooseItem(models.Model):
    section = models.ForeignKey(
        HomeWhyChooseSection,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Khối",
    )
    icon = models.CharField(
        max_length=100,
        default="fa-solid fa-star",
        verbose_name="Icon Font Awesome",
        help_text="Ví dụ: fa fa-trophy hoặc fa-solid fa-shield",
    )
    title = models.CharField(max_length=255, verbose_name="Tiêu đề item")
    content = models.TextField(verbose_name="Nội dung item")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name = "Lý do chọn chúng tôi"
        verbose_name_plural = "Lý do chọn chúng tôi"

    def __str__(self):
        return self.title


############# AboutStatementType
class AboutStatementType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Tên loại")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at", "name"]
        verbose_name = "Loại tầm nhìn / sứ mệnh"
        verbose_name_plural = "Loại tầm nhìn / sứ mệnh"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "loai-noi-dung"
            slug = base_slug
            counter = 1
            while (
                AboutStatementType.objects.exclude(pk=self.pk)
                .filter(slug=slug)
                .exists()
            ):
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


###################
###Nguyễn Tấn Hoàng AboutStatement
class AboutStatement(models.Model):
    title = models.CharField(
        max_length=150,
        blank=True,
        default="",
        verbose_name="Tiêu đề",
        help_text="Có thể để trống để dùng tên loại nội dung.",
    )
    statement_type = models.ForeignKey(
        AboutStatementType,
        on_delete=models.PROTECT,
        related_name="statements",
        verbose_name="Loại nội dung",
    )
    content = models.TextField(verbose_name="Nội dung")
    icon = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Icon Font Awesome / Icon URL",
        help_text=(
            "Có thể nhập fa-eye, fa-solid fa-eye, cart-arrow-down "
            "hoặc URL icon từ Font Awesome."
        ),
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự hiển thị")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name = "Nội dung tầm nhìn / sứ mệnh"
        verbose_name_plural = "Nội dung tầm nhìn / sứ mệnh"

    @property
    def display_title(self):
        return (self.title or "").strip() or self.statement_type.name

    @property
    def icon_css_class(self):
        raw = (self.icon or "").strip()
        fallback = "fa-solid fa-star"

        if not raw:
            return fallback

        raw_lower = raw.lower()

        if "fontawesome.com/" in raw_lower:
            parsed = urlparse(raw)
            path_parts = [part for part in parsed.path.split("/") if part]
            icon_name = path_parts[-1] if path_parts else "star"
            query = parse_qs(parsed.query)
            style = (query.get("s", ["solid"])[0] or "solid").lower()
            style_map = {
                "solid": "fa-solid",
                "regular": "fa-regular",
                "brands": "fa-brands",
                "brand": "fa-brands",
                "light": "fa-light",
                "thin": "fa-thin",
                "duotone": "fa-duotone",
            }
            prefix = style_map.get(style, "fa-solid")
            return f"{prefix} fa-{icon_name}"

        parts = raw.split()
        known_prefixes = {
            "fa-solid",
            "fa-regular",
            "fa-brands",
            "fa-light",
            "fa-thin",
            "fa-duotone",
            "fa",
            "fab",
            "far",
            "fas",
        }

        if any(part in known_prefixes for part in parts):
            if raw.startswith("fa ") and len(parts) >= 2 and parts[1].startswith("fa-"):
                return f"fa-solid {parts[1]}"
            return raw

        if raw.startswith("fa-"):
            return f"fa-solid {raw}"

        if "-" in raw and " " not in raw:
            return f"fa-solid fa-{raw}"

        return fallback

    def __str__(self):
        return f"{self.statement_type.name} - {self.display_title}"


############## ServiceType
class ServiceType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Tên loại")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at", "name"]
        verbose_name = "Loại dịch vụ"
        verbose_name_plural = "Loại dịch vụ"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "loai-dich-vu"
            slug = base_slug
            counter = 1
            while ServiceType.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


############## Service
class Service(models.Model):
    service_type = models.ForeignKey(
        ServiceType,
        on_delete=models.PROTECT,
        related_name="services",
        verbose_name="Loại dịch vụ",
    )
    title = models.CharField(max_length=150, verbose_name="Tiêu đề")
    content = models.TextField(verbose_name="Nội dung")
    icon = models.CharField(
        max_length=500,
        blank=True,
        default="",
        verbose_name="Icon Font Awesome / Icon URL",
        help_text=(
            "Có thể nhập fa-eye, fa-solid fa-eye, cart-arrow-down "
            "hoặc URL icon từ Font Awesome."
        ),
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự hiển thị")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name = "Dịch vụ"
        verbose_name_plural = "Dịch vụ"

    @property
    def icon_css_class(self):
        raw = (self.icon or "").strip()
        fallback = "fa-solid fa-star"

        if not raw:
            return fallback

        raw_lower = raw.lower()

        if "fontawesome.com/" in raw_lower:
            parsed = urlparse(raw)
            path_parts = [part for part in parsed.path.split("/") if part]
            icon_name = path_parts[-1] if path_parts else "star"
            query = parse_qs(parsed.query)
            style = (query.get("s", ["solid"])[0] or "solid").lower()
            style_map = {
                "solid": "fa-solid",
                "regular": "fa-regular",
                "brands": "fa-brands",
                "brand": "fa-brands",
                "light": "fa-light",
                "thin": "fa-thin",
                "duotone": "fa-duotone",
            }
            prefix = style_map.get(style, "fa-solid")
            return f"{prefix} fa-{icon_name}"

        parts = raw.split()
        known_prefixes = {
            "fa-solid",
            "fa-regular",
            "fa-brands",
            "fa-light",
            "fa-thin",
            "fa-duotone",
            "fa",
            "fab",
            "far",
            "fas",
        }

        if any(part in known_prefixes for part in parts):
            if raw.startswith("fa ") and len(parts) >= 2 and parts[1].startswith("fa-"):
                return f"fa-solid {parts[1]}"
            return raw

        if raw.startswith("fa-"):
            return f"fa-solid {raw}"

        if "-" in raw and " " not in raw:
            return f"fa-solid fa-{raw}"

        return fallback

    def __str__(self):
        return self.title


# chứng chỉ và năng lực
class Certificate(ManagedMediaCleanupModel):
    managed_file_fields = ("image",)

    ICON_CHOICES = [
        ("fa-certificate", "Giấy chứng nhận"),
        ("fa-shield", "Shield"),
        ("fa-leaf", "Leaf"),
        ("fa-building-o", "Building"),
        ("fa-trophy", "Trophy"),
        ("fa-star", "Star"),
        ("fa-check-circle", "Check Circle"),
        ("fa-globe", "Globe"),
    ]

    title = models.CharField(max_length=300, verbose_name="Tiêu đề")
    description = models.TextField(verbose_name="Mô tả")
    icon = models.CharField(
        max_length=50,
        choices=ICON_CHOICES,
        default="fa-certificate",
        verbose_name="Icon",
    )
    image = models.ImageField(
        upload_to="certificates/",
        blank=True,
        null=True,
        verbose_name="Hình ảnh chứng chỉ",
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]

    def __str__(self):
        return self.title


class ContactInfo(models.Model):
    branch_name = models.CharField(
        max_length=150, verbose_name="Tên chi nhánh / văn phòng"
    )
    address = models.TextField(verbose_name="Địa chỉ")
    phone = models.CharField(max_length=50, verbose_name="Số điện thoại")
    fax = models.CharField(max_length=50, blank=True, verbose_name="Fax")
    email = models.EmailField(blank=True, verbose_name="Email")
    working_hours = models.CharField(
        max_length=255, blank=True, verbose_name="Giờ làm việc"
    )

    # Giữ lại field này để dùng khi cần, nhưng từ giờ có thể để trống
    map_embed_url = models.URLField(blank=True, verbose_name="Link Google Maps Embed")

    facebook_url = models.URLField(blank=True, verbose_name="Facebook URL")
    youtube_url = models.URLField(blank=True, verbose_name="YouTube URL")
    linkedin_url = models.URLField(blank=True, verbose_name="LinkedIn URL")
    instagram_url = models.URLField(blank=True, verbose_name="Instagram URL")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự hiển thị")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]

    @property
    def map_display_url(self):
        # Nếu admin có nhập link embed chuẩn thì dùng luôn
        raw_url = (self.map_embed_url or "").strip()
        if raw_url and ("/maps/embed" in raw_url or "output=embed" in raw_url):
            return raw_url

        # Nếu không có link map, chỉ cần dùng địa chỉ
        query = (self.address or "").strip()
        if not query:
            return ""

        return (
            "https://maps.google.com/maps?"
            f"q={quote_plus(query)}&t=&z=15&ie=UTF8&iwloc=&output=embed"
        )

    def __str__(self):
        return self.branch_name


class EmailOTPSettings(models.Model):
    sender_name = models.CharField(
        max_length=150,
        blank=True,
        default="Sao Bac Dau Construction",
        verbose_name="Tên hiển thị email gửi OTP",
    )
    sender_email = models.EmailField(blank=True, default="", verbose_name="Email gửi OTP")
    smtp_host = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="SMTP host",
    )
    smtp_port = models.PositiveIntegerField(default=587, verbose_name="SMTP port")
    smtp_username = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="SMTP username",
    )
    smtp_password = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="SMTP password / app password",
    )
    use_tls = models.BooleanField(default=True, verbose_name="Dùng TLS")
    use_ssl = models.BooleanField(default=False, verbose_name="Dùng SSL")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cấu hình email OTP"
        verbose_name_plural = "Cấu hình email OTP"

    @classmethod
    def get_solo(cls):
        config = cls.objects.order_by("id").first()
        if config is None:
            config = cls.objects.create(
                sender_email="",
                smtp_host="smtp.gmail.com",
                smtp_port=587,
                smtp_username="",
                smtp_password="",
                use_tls=True,
                use_ssl=False,
            )
        return config

    @property
    def from_email(self):
        display_name = (self.sender_name or "").strip()
        email = (self.sender_email or "").strip()
        if display_name and email:
            return f"{display_name} <{email}>"
        return email

    def __str__(self):
        return self.sender_email or "Chưa cấu hình email OTP"


class PasswordOTP(models.Model):
    PURPOSE_CHOICES = [
        ("forgot_password", "Quên mật khẩu"),
        ("change_password", "Đổi mật khẩu"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_otps",
    )
    email = models.EmailField(verbose_name="Email nhận OTP")
    purpose = models.CharField(max_length=30, choices=PURPOSE_CHOICES)
    code = models.CharField(max_length=6, verbose_name="Mã OTP")
    expires_at = models.DateTimeField(verbose_name="Hết hạn lúc")
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "OTP đổi mật khẩu"
        verbose_name_plural = "OTP đổi mật khẩu"

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"{self.user.username} - {self.purpose} - {self.code}"


class Consultation(models.Model):
    PROJECT_TYPE_CHOICES = [
        ("dan-dung", "Xây dựng Dân dụng (Nhà ở, Biệt thự, Chung cư)"),
        ("cong-nghiep", "Xây dựng Công nghiệp (Nhà máy, Kho xưởng)"),
        ("thuong-mai", "Xây dựng Thương mại (Văn phòng, TTTM)"),
        ("ha-tang", "Hạ tầng Kỹ thuật (Đường, Cầu, Cống)"),
        ("noi-that", "Thi công Nội thất"),
        ("thiet-ke", "Thiết kế Kiến trúc & Kết cấu"),
        ("khac", "Khác"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150, blank=True, default="")
    phone = models.CharField(max_length=50, default="")
    email = models.EmailField(blank=True)
    project_type = models.CharField(
        max_length=50,
        default="",
        choices=PROJECT_TYPE_CHOICES,
    )
    subject = models.CharField(max_length=255, default="")
    budget = models.CharField(max_length=100, blank=True, default="")
    content = models.TextField(blank=True)

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("done", "Done"),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    handled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="handled_consultations",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.subject or f"Yeu cau #{self.pk}"


class Notification(models.Model):

    NOTIFICATION_TYPES = [("consult", "Consultation"), ("answer", "Answer")]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )

    message = models.TextField()

    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)

    # 🔥 liên kết tới yêu cầu
    consultation = models.ForeignKey(
        Consultation, on_delete=models.CASCADE, null=True, blank=True
    )

    is_read = models.BooleanField(default=False)

    link = models.CharField(max_length=255, blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return f"{self.user.username} - {self.message[:30]}"

#carousel va video ảnh nền
class HeroSection(ManagedMediaCleanupModel):
    managed_file_fields = ("bg_image", "bg_video")

    # Text content
    badge_text = models.CharField(max_length=200, verbose_name="Badge text (vd: Hơn 15 năm...)")
    heading_line1 = models.CharField(max_length=300, verbose_name="Tiêu đề dòng 1")
    heading_line2 = models.CharField(max_length=300, blank=True, verbose_name="Tiêu đề dòng 2 (vàng)")
    description = models.TextField(verbose_name="Mô tả")
    btn_primary_text = models.CharField(max_length=100, default="Giới Thiệu", verbose_name="Nút chính - text")
    btn_primary_url = models.CharField(max_length=200, default="/about/", verbose_name="Nút chính - URL")
    btn_outline_text = models.CharField(max_length=100, default="Xem Dự Án", verbose_name="Nút phụ - text")
    btn_outline_url = models.CharField(max_length=200, default="/project/", verbose_name="Nút phụ - URL")

    # Stats
    stat_1_num = models.CharField(max_length=20, default="500+")
    stat_1_label = models.CharField(max_length=100, default="Dự án hoàn thành")
    stat_2_num = models.CharField(max_length=20, default="15+")
    stat_2_label = models.CharField(max_length=100, default="Năm kinh nghiệm")
    stat_3_num = models.CharField(max_length=20, default="200+")
    stat_3_label = models.CharField(max_length=100, default="Kỹ sư & Chuyên gia")
    stat_4_num = models.CharField(max_length=20, default="98%")
    stat_4_label = models.CharField(max_length=100, default="Khách hàng hài lòng")

    # Background
    BG_TYPE_CHOICES = [
        ('color', 'Màu nền (mặc định)'),
        ('image', 'Ảnh nền'),
        ('video', 'Video tự chạy'),
        ('carousel', 'Carousel nhiều ảnh'),
    ]
    TEXT_THEME_CHOICES = [
        ('light', 'Chữ sáng'),
        ('dark', 'Chữ tối'),
    ]
    bg_type = models.CharField(max_length=20, choices=BG_TYPE_CHOICES, default='color', verbose_name="Loại nền")
    bg_image = models.ImageField(upload_to='hero/', blank=True, null=True, verbose_name="Ảnh nền")
    bg_video = models.FileField(upload_to='hero/videos/', blank=True, null=True, verbose_name="Video nền (mp4)")
    text_theme = models.CharField(max_length=10, choices=TEXT_THEME_CHOICES, default='light', verbose_name="Theme màu chữ")

    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hero Section"

    def __str__(self):
        return self.heading_line1


class HeroCarouselImage(ManagedMediaCleanupModel):
    managed_file_fields = ("image",)

    hero = models.ForeignKey(HeroSection, on_delete=models.CASCADE, related_name='carousel_images')
    image = models.ImageField(upload_to='hero/carousel/', verbose_name="Ảnh")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Carousel ảnh #{self.order}"


class Partner(ManagedMediaCleanupModel):
    managed_file_fields = ("logo",)

    name = models.CharField(max_length=200, verbose_name="Tên đối tác")
    logo = models.ImageField(
        upload_to="partners/",
        blank=True,
        null=True,
        verbose_name="Logo",
    )
    website_url = models.URLField(blank=True, verbose_name="Website")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự hiển thị")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "created_at"]
        verbose_name = "Đối tác"
        verbose_name_plural = "Đối tác"

    def __str__(self):
        return self.name


class SiteBrandSettings(ManagedMediaCleanupModel):
    managed_file_fields = ("logo_image", "preloader_image")

    LOGO_TYPE_ICON = "icon"
    LOGO_TYPE_IMAGE = "image"
    LOGO_TYPE_CHOICES = [
        (LOGO_TYPE_ICON, "Icon Font Awesome"),
        (LOGO_TYPE_IMAGE, "Hình ảnh"),
    ]

    logo_type = models.CharField(
        max_length=20,
        choices=LOGO_TYPE_CHOICES,
        default=LOGO_TYPE_ICON,
        verbose_name="Kiểu logo",
    )
    logo_image = models.ImageField(
        upload_to="branding/",
        blank=True,
        null=True,
        verbose_name="Ảnh logo",
    )
    preloader_image = models.ImageField(
        upload_to="branding/preloader/",
        blank=True,
        null=True,
        verbose_name="Ảnh màn hình loading",
    )
    logo_icon = models.CharField(
        max_length=500,
        blank=True,
        default="fa-solid fa-star",
        verbose_name="Tên class / link icon Font Awesome",
        help_text=(
            "Có thể nhập fa-star, fa-solid fa-star, star "
            "hoặc link icon từ Font Awesome."
        ),
    )
    brand_name = models.CharField(
        max_length=200,
        default="Sao Bắc Đẩu",
        verbose_name="Tên thương hiệu",
    )
    brand_subtitle = models.CharField(
        max_length=200,
        default="Construction",
        verbose_name="Dòng phụ thương hiệu",
    )
    footer_bottom_text = models.CharField(
        max_length=300,
        default="© 2026 Công Ty Xây Dựng Sao Bắc Đẩu | MST: 0123456789",
        verbose_name="Nội dung footer bottom",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cấu hình thương hiệu"
        verbose_name_plural = "Cấu hình thương hiệu"

    @classmethod
    def get_solo(cls):
        config = cls.objects.order_by("id").first()
        if config is None:
            config = cls.objects.create()
        return config

    @property
    def icon_css_class(self):
        raw = (self.logo_icon or "").strip()
        fallback = "fa-solid fa-star"

        if not raw:
            return fallback

        raw_lower = raw.lower()

        if "fontawesome.com/" in raw_lower:
            parsed = urlparse(raw)
            path_parts = [part for part in parsed.path.split("/") if part]
            icon_name = path_parts[-1] if path_parts else "star"
            query = parse_qs(parsed.query)
            style = (query.get("s", ["solid"])[0] or "solid").lower()
            style_map = {
                "solid": "fa-solid",
                "regular": "fa-regular",
                "brands": "fa-brands",
                "brand": "fa-brands",
                "light": "fa-light",
                "thin": "fa-thin",
                "duotone": "fa-duotone",
            }
            prefix = style_map.get(style, "fa-solid")
            return f"{prefix} fa-{icon_name}"

        parts = raw.split()
        known_prefixes = {
            "fa-solid",
            "fa-regular",
            "fa-brands",
            "fa-light",
            "fa-thin",
            "fa-duotone",
            "fa",
            "fab",
            "far",
            "fas",
        }

        if any(part in known_prefixes for part in parts):
            if raw.startswith("fa ") and len(parts) >= 2 and parts[1].startswith("fa-"):
                return f"fa-solid {parts[1]}"
            return raw

        if raw.startswith("fa-"):
            return f"fa-solid {raw}"

        if "-" in raw and " " not in raw:
            return f"fa-solid fa-{raw}"

        return fallback

    @property
    def has_logo_image(self):
        return bool(self.logo_image and getattr(self.logo_image, "url", ""))

    @property
    def has_preloader_image(self):
        return bool(self.preloader_image and getattr(self.preloader_image, "url", ""))

    def __str__(self):
        return self.brand_name or "Cấu hình thương hiệu"


class OfficeRental(ManagedMediaCleanupModel):
    managed_file_fields = ("image",)

    title = models.CharField(max_length=200, verbose_name="Tên văn phòng")
    summary = models.TextField(blank=True, verbose_name="Mô tả ngắn")
    content = models.TextField(verbose_name="Thông tin chi tiết")
    image = models.ImageField(
        upload_to="office_rentals/",
        blank=True,
        null=True,
        verbose_name="Ảnh văn phòng",
    )
    area = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Diện tích (m2)",
    )
    rent_price = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        verbose_name="Giá thuê (VNĐ)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Cho thuê văn phòng"
        verbose_name_plural = "Cho thuê văn phòng"

    def __str__(self):
        return self.title


class EducationSpaceDesign(ManagedMediaCleanupModel):
    managed_file_fields = ("image",)

    title = models.CharField(max_length=200, verbose_name="Tiêu đề")
    summary = models.TextField(blank=True, verbose_name="Mô tả ngắn")
    content = models.TextField(verbose_name="Nội dung chi tiết")
    image = models.ImageField(
        upload_to="education_spaces/",
        blank=True,
        null=True,
        verbose_name="Ảnh minh họa",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "Thiết kế không gian giáo dục"
        verbose_name_plural = "Thiết kế không gian giáo dục"

    def __str__(self):
        return self.title
