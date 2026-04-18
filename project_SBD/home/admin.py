from django.contrib import admin
from .models import (
    Product,
    ProductCategory,
    Project,
    ProjectCategory,
    Post,
    PostCategory,
    FAQ,
    LeadershipMember,
    AboutStatement,
    ContactInfo,
    Notification,
    Consultation,
)

admin.site.register(ProjectCategory)
admin.site.register(ProductCategory)

admin.site.register(Post)
admin.site.register(PostCategory)

admin.site.register(FAQ)
admin.site.register(LeadershipMember)

admin.site.register(AboutStatement)

admin.site.register(ContactInfo)
admin.site.register(Notification)
admin.site.register(Consultation)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "is_featured")
    list_filter = ("is_featured", "category")
    list_editable = ("is_featured",)


# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ("name", "category", "created_at")
#     list_filter = ("category",)
#     search_fields = ("name",)
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "supplier_name", "created_at")
    list_filter = ("category",)
    search_fields = ("name", "supplier_name", "supplier_address")
