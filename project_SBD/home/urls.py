from django.urls import path
from . import views

urlpatterns = [
    # PUBLIC
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('project/', views.project, name='project'),
    path('project/<int:id>/', views.project_detail, name='project_detail'),
    path('product/', views.product_public, name='product'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),

    # AUTH
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    # DASHBOARD
    path('dashboard/', views.dashboard, name='dashboard'),

    # CRUD
    # project
    path('project/add/', views.project_create, name='project_add'),
    path('project/edit/<int:id>/', views.project_update, name='project_edit'),
    path('project/delete/<int:id>/', views.project_delete, name='project_delete'),

    # product
    path('products/', views.product_list, name='product_list'),
    path('product/add/', views.product_create, name='product_add'),
    path('product/edit/<int:id>/', views.product_update, name='product_edit'),
    path('product/delete/<int:id>/', views.product_delete, name='product_delete'),

    # project category
    path('project-category/', views.project_category_list, name='project_category_list'),
    path('project-category/add/', views.project_category_create, name='project_category_add'),
    path('project-category/edit/<int:id>/', views.project_category_update, name='project_category_edit'),
    path('project-category/delete/<int:id>/', views.project_category_delete, name='project_category_delete'),

    # product category
    path('product-category/', views.product_category_list, name='product_category_list'),
    path('product-category/add/', views.product_category_create, name='product_category_add'),
    path('product-category/edit/<int:id>/', views.product_category_update, name='product_category_edit'),
    path('product-category/delete/<int:id>/', views.product_category_delete, name='product_category_delete'),
]
