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
    Consultation
)

# Register your models here.
admin.site.register(Project)
admin.site.register(ProjectCategory)
admin.site.register(Product)
admin.site.register(ProductCategory)
#########################
admin.site.register(Post)
admin.site.register(PostCategory)

########################
admin.site.register(FAQ)
admin.site.register(LeadershipMember)
#################
admin.site.register(AboutStatement)

admin.site.register(ContactInfo)
admin.site.register(Notification)
admin.site.register(Consultation)
