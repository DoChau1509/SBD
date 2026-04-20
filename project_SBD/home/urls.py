from django.urls import path
from . import views

urlpatterns = [
    # PUBLIC
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("project/", views.project, name="project"),
    path("project/<int:id>/", views.project_detail, name="project_detail"),
    path("product/", views.product_public, name="product"),
    path("product/<int:id>/", views.product_detail, name="product_detail"),
    path("post/", views.post_public, name="post"),
    path("post/<int:id>/", views.post_detail, name="post_detail"),
    # AUTH
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    # DASHBOARD
    path("dashboard/", views.dashboard, name="dashboard"),
    # CRUD
    # project
    path("project/add/", views.project_create, name="project_add"),
    path("project/edit/<int:id>/", views.project_update, name="project_edit"),
    path("project/delete/<int:id>/", views.project_delete, name="project_delete"),
    path(
        "project/featured/",
        views.featured_project_list,
        name="featured_project_list",
    ),
    # product
    path("products/", views.product_list, name="product_list"),
    path("product/add/", views.product_create, name="product_add"),
    path("product/edit/<int:id>/", views.product_update, name="product_edit"),
    path("product/delete/<int:id>/", views.product_delete, name="product_delete"),
    # post
    path("posts/", views.post_list, name="post_list"),
    path("post/add/", views.post_create, name="post_add"),
    path("post/edit/<int:id>/", views.post_update, name="post_edit"),
    path("post/delete/<int:id>/", views.post_delete, name="post_delete"),
    # project category
    path(
        "project-category/", views.project_category_list, name="project_category_list"
    ),
    path(
        "project-category/add/",
        views.project_category_create,
        name="project_category_add",
    ),
    path(
        "project-category/edit/<int:id>/",
        views.project_category_update,
        name="project_category_edit",
    ),
    path(
        "project-category/delete/<int:id>/",
        views.project_category_delete,
        name="project_category_delete",
    ),
    # product category
    path(
        "product-category/", views.product_category_list, name="product_category_list"
    ),
    path(
        "product-category/add/",
        views.product_category_create,
        name="product_category_add",
    ),
    path(
        "product-category/edit/<int:id>/",
        views.product_category_update,
        name="product_category_edit",
    ),
    path(
        "product-category/delete/<int:id>/",
        views.product_category_delete,
        name="product_category_delete",
    ),
    # post category
    path("post-category/", views.post_category_list, name="post_category_list"),
    path("post-category/add/", views.post_category_create, name="post_category_add"),
    path(
        "post-category/edit/<int:id>/",
        views.post_category_update,
        name="post_category_edit",
    ),
    path(
        "post-category/delete/<int:id>/",
        views.post_category_delete,
        name="post_category_delete",
    ),
    # faq
    path("faqs/", views.faq_list, name="faq_list"),
    path("faq/add/", views.faq_create, name="faq_add"),
    path("faq/edit/<int:id>/", views.faq_update, name="faq_edit"),
    path("faq/delete/<int:id>/", views.faq_delete, name="faq_delete"),
    # leadership
    path("leadership/", views.leadership_list, name="leadership_list"),
    path("leadership/add/", views.leadership_create, name="leadership_add"),
    path("leadership/edit/<int:id>/", views.leadership_update, name="leadership_edit"),
    path(
        "leadership/delete/<int:id>/", views.leadership_delete, name="leadership_delete"
    ),
    # about statement types
    path(
        "about-statement-types/",
        views.statement_type_list,
        name="statement_type_list",
    ),
    path(
        "about-statement-types/add/",
        views.statement_type_create,
        name="statement_type_add",
    ),
    path(
        "about-statement-types/edit/<int:id>/",
        views.statement_type_update,
        name="statement_type_edit",
    ),
    path(
        "about-statement-types/delete/<int:id>/",
        views.statement_type_delete,
        name="statement_type_delete",
    ),
    # about statements
    path("about-statements/", views.statement_list, name="statement_list"),
    path("about-statements/add/", views.statement_create, name="statement_add"),
    path(
        "about-statements/edit/<int:id>/", views.statement_update, name="statement_edit"
    ),
    path(
        "about-statements/delete/<int:id>/",
        views.statement_delete,
        name="statement_delete",
    ),
    # certificate
    path("certificates/", views.certificate_list, name="certificate_list"),
    path("certificate/add/", views.certificate_create, name="certificate_add"),
    path(
        "certificate/edit/<int:id>/", views.certificate_update, name="certificate_edit"
    ),
    path(
        "certificate/delete/<int:id>/",
        views.certificate_delete,
        name="certificate_delete",
    ),
    # contact info
    path("contact-infos/", views.contact_info_list, name="contact_info_list"),
    path("contact-info/add/", views.contact_info_create, name="contact_info_add"),
    path(
        "contact-info/edit/<int:pk>/",
        views.contact_info_update,
        name="contact_info_edit",
    ),
    path(
        "contact-info/delete/<int:id>/",
        views.contact_info_delete,
        name="contact_info_delete",
    ),
    path(
        "contact-info/<int:pk>/toggle-status/",
        views.contact_info_toggle_status,
        name="contact_info_toggle_status",
    ),
    path("consultations/", views.consultation_list, name="consultation_list"),
    path(
        "consultations/<int:id>/",
        views.consultation_detail,
        name="consultation_detail",
    ),
    path("notifications/", views.notifications, name="notifications"),
    path(
        "notifications/<int:id>/read/",
        views.notification_read,
        name="notification_read",
    ),
    path(
        "notifications/mark-all-read/",
        views.notification_mark_all_read,
        name="notification_mark_all_read",
    ),
    path("about-intro/", views.about_intro_edit, name="about_intro_edit"),
    path("about-video-tour/", views.about_video_tour_edit, name="about_video_tour_edit"),
    # service types
    path("service-types/", views.service_type_list, name="service_type_list"),
    path("service-types/add/", views.service_type_create, name="service_type_add"),
    path(
        "service-types/edit/<int:id>/",
        views.service_type_update,
        name="service_type_edit",
    ),
    path(
        "service-types/delete/<int:id>/",
        views.service_type_delete,
        name="service_type_delete",
    ),
    # services
    path("services/", views.service_list, name="service_list"),
    path("services/add/", views.service_create, name="service_add"),
    path("services/edit/<int:id>/", views.service_update, name="service_edit"),
    path("services/delete/<int:id>/", views.service_delete, name="service_delete"),
    # Why-choose
    path(
        "why-choose/edit/",
        views.why_choose_section_edit,
        name="why_choose_section_edit",
    ),
    path("why-choose/items/", views.why_choose_item_list, name="why_choose_item_list"),
    path(
        "why-choose/items/add/",
        views.why_choose_item_create,
        name="why_choose_item_add",
    ),
    path(
        "why-choose/items/<int:id>/edit/",
        views.why_choose_item_update,
        name="why_choose_item_edit",
    ),
    path(
        "why-choose/items/<int:id>/delete/",
        views.why_choose_item_delete,
        name="why_choose_item_delete",
    ),
    path('hero/', views.hero_edit, name='hero_edit'),
    path('hero/carousel/delete/<int:id>/', views.hero_carousel_delete, name='hero_carousel_delete'),
]
