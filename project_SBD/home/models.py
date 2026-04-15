from django.db import models

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
    image = models.ImageField(upload_to='projects/')
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(
        ProjectCategory,
        on_delete=models.PROTECT,
        related_name='projects',
    )

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.PROTECT,
        related_name='products',
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
    image = models.ImageField(upload_to='posts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(
        PostCategory,
        on_delete=models.PROTECT,
        related_name='posts',
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
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.question
    
###### Trịnh gia đạt làm phần dữ liệu, thêm xóa sửa phần ban lãnh đạo trong trang giới thiệu
class LeadershipMember(models.Model):
    full_name = models.CharField(max_length=150, verbose_name="Họ và tên")
    role = models.CharField(max_length=150, verbose_name="Chức vụ")
    bio = models.TextField(verbose_name="Mô tả ngắn")
    image = models.ImageField(upload_to='leadership/', blank=True, null=True, verbose_name="Ảnh")
    initials = models.CharField(max_length=10, blank=True, verbose_name="Chữ viết tắt")
    linkedin_url = models.URLField(blank=True, verbose_name="LinkedIn URL")
    facebook_url = models.URLField(blank=True, verbose_name="Facebook URL")
    instagram_url = models.URLField(blank=True, verbose_name="Instagram URL")
    order = models.PositiveIntegerField(default=0, verbose_name="Thứ tự hiển thị")
    is_active = models.BooleanField(default=True, verbose_name="Hiển thị")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.full_name