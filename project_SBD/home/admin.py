from django.contrib import admin
from .models import Product, ProductCategory, Project, ProjectCategory, Post, PostCategory

# Register your models here.
admin.site.register(Project)
admin.site.register(ProjectCategory)
admin.site.register(Product)
admin.site.register(ProductCategory)
#########################
admin.site.register(Post)
admin.site.register(PostCategory)
