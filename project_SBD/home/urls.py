from django.urls import path
from . import views

urlpatterns = [
    # PUBLIC
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('project/', views.project, name='project'),
    path('project/<int:id>/', views.project_detail, name='project_detail'),

    # AUTH
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # DASHBOARD
    path('dashboard/', views.dashboard, name='dashboard'),

    # CRUD
    path('project/add/', views.project_create, name='project_add'),
    path('project/edit/<int:id>/', views.project_update, name='project_edit'),
    path('project/delete/<int:id>/', views.project_delete, name='project_delete'),
]