from django.db import models
from django.contrib.auth.models import User


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


###Nguyễn Tấn Hoàng
class AboutStatement(models.Model):
    STATEMENT_TYPE_CHOICES = (
        ("vision", "Tầm nhìn"),
        ("mission", "Sứ mệnh"),
    )

    title = models.CharField(max_length=150, verbose_name="Tiêu đề")
    statement_type = models.CharField(
        max_length=20,
        choices=STATEMENT_TYPE_CHOICES,
        verbose_name="Loại nội dung",
    )
    content = models.TextField(verbose_name="Nội dung")
    icon = models.CharField(
        max_length=50,
        blank=True,
        default="fa-star",
        verbose_name="Icon Font Awesome",
        help_text="Ví dụ: fa-eye, fa-rocket",
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự hiển thị")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["statement_type", "order", "created_at"]

    def __str__(self):
        return f"{self.get_statement_type_display()} - {self.title}"


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
    SIDE_CHOICES = [
        ("left", "Trái"),
        ("right", "Phải"),
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
    side = models.CharField(
        max_length=10, choices=SIDE_CHOICES, default="left", verbose_name="Cột"
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["side", "order", "created_at"]

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

    def __str__(self):
        return self.branch_name

class Consultation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('done', 'Done'),
    ]

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    handled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='handled_consultations'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class Notification(models.Model):

    NOTIFICATION_TYPES = [
        ('consult', 'Consultation'),
        ('answer', 'Answer')
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    message = models.TextField()

    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
    )

    # 🔥 liên kết tới yêu cầu
    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    is_read = models.BooleanField(default=False)

    link = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f"{self.user.username} - {self.message[:30]}"