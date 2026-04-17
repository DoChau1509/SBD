from django.db import models
from urllib.parse import quote_plus, urlparse, parse_qs
from django.contrib.auth.models import User
from django.utils.text import slugify


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


class Project(models.Model):
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


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name="products",
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


class Post(models.Model):
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
class LeadershipMember(models.Model):
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
    kicker = models.CharField(max_length=100, default="Thành lập 2009", verbose_name="Dòng nhỏ trên cùng")
    brand_name = models.CharField(max_length=200, default="Sao Bắc Đẩu", verbose_name="Tên thương hiệu")
    slogan = models.CharField(max_length=300, default="Chất lượng — Uy tín — Bền vững", verbose_name="Slogan")
    highlight_1 = models.CharField(max_length=100, blank=True, verbose_name="Highlight 1 (vd: ISO 9001:2015)")
    highlight_2 = models.CharField(max_length=100, blank=True, verbose_name="Highlight 2 (vd: 200+ kỹ sư)")
    highlight_3 = models.CharField(max_length=100, blank=True, verbose_name="Highlight 3 (vd: Thi công toàn quốc)")
    badge_number = models.CharField(max_length=20, default="500+", verbose_name="Số badge (vd: 500+)")
    badge_text = models.CharField(max_length=100, default="Dự Án Hoàn Thành", verbose_name="Chữ dưới badge")

    # Cột phải (text)
    heading = models.CharField(max_length=300, default="Công Ty Xây Dựng Sao Bắc Đẩu", verbose_name="Tiêu đề lớn")
    paragraph_1 = models.TextField(verbose_name="Đoạn văn 1")
    paragraph_2 = models.TextField(blank=True, verbose_name="Đoạn văn 2")

    # Danh sách bullet (mỗi dòng 1 item)
    bullet_points = models.TextField(
        verbose_name="Danh sách điểm mạnh",
        help_text="Mỗi dòng là một bullet. VD: Chứng nhận ISO 9001:2015"
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Giới thiệu công ty"

    def __str__(self):
        return self.heading

    def get_bullets(self):
        """Trả về list các bullet, bỏ dòng trống"""
        return [line.strip() for line in self.bullet_points.splitlines() if line.strip()]

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


# chứng chỉ và năng lực
class Certificate(models.Model):
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
