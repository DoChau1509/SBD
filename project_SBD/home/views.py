# views.py
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Project


# ====================== PUBLIC PAGES ======================
def home(request):
    return render(request, 'home/home.html')


def about(request):
    return render(request, 'home/about.html')


def contact(request):
    return render(request, 'home/contact.html')


def project(request):
    projects = Project.objects.all()
    return render(request, 'home/project.html', {'projects': projects})


def project_detail(request, id):
    project = get_object_or_404(Project, id=id)
    return render(request, 'home/project_detail.html', {'project': project})


# ====================== CRUD PROJECT ======================
@login_required
def project_create(request):
    if request.method == 'POST':
        Project.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            image=request.FILES.get('image')
        )
        return redirect('dashboard')

    return render(request, 'home/project_form.html')


@login_required
def project_update(request, id):
    project = get_object_or_404(Project, id=id)

    if request.method == 'POST':
        project.name = request.POST.get('name')
        project.description = request.POST.get('description')
        if 'image' in request.FILES:
            project.image = request.FILES['image']
        project.save()  # ← Quan trọng: phải có save()
        return redirect('dashboard')

    return render(request, 'home/project_form.html', {'project': project})


@login_required
def project_delete(request, id):
    project = get_object_or_404(Project, id=id)
    project.delete()
    return redirect('dashboard')  # Nên redirect về dashboard thay vì home


# ====================== AUTH ======================
def login_view(request):
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password')
        )
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            # Có thể thêm message lỗi sau
            pass
    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def dashboard(request):
    projects = Project.objects.all().order_by('-id')
    return render(request, 'home/dashboard.html', {'projects': projects})