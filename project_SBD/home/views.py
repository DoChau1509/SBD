# views.py
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models.deletion import ProtectedError
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.text import slugify
from django.utils.http import url_has_allowed_host_and_scheme
from functools import wraps
from urllib.parse import urlparse
from .forms import UserRegistrationForm, LoginForm

from .models import (
    Product,
    ProductCategory,
    Project,
    ProjectCategory,
)


def staff_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/login/?next={request.path}")

        if request.user.is_staff or request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        messages.warning(request, "Bạn không có quyền truy cập trang quản lý.")
        return redirect("home")

    return _wrapped


def _is_management_path(path: str) -> bool:
    if not path:
        return False

    management_prefixes = (
        "/dashboard",
        "/project/add",
        "/project/edit",
        "/project/delete",
        "/products",
        "/product/add",
        "/product/edit",
        "/product/delete",
        "/project-category",
        "/product-category",
    )
    return path.startswith(management_prefixes)


# ====================== PUBLIC PAGES ======================
def home(request):
    return render(request, 'home/home.html')


def about(request):
    return render(request, 'home/about.html')


def contact(request):
    return render(request, 'home/contact.html')


def project(request):
    categories = ProjectCategory.objects.filter(is_hidden=False).order_by("name")
    projects = Project.objects.select_related("category").all().order_by("-created_at", "-id")
    return render(
        request,
        "home/project.html",
        {"projects": projects, "categories": categories},
    )


def project_detail(request, id):
    project = get_object_or_404(Project, id=id)
    return render(request, 'home/project_detail.html', {'project': project})


# ====================== CRUD PROJECT ======================
def _get_default_project_category():
    category, _ = ProjectCategory.objects.get_or_create(
        name="Chưa phân loại",
        defaults={"slug": "uncategorized", "is_hidden": True},
    )
    return category


def _get_default_product_category():
    category, _ = ProductCategory.objects.get_or_create(
        name="Chưa phân loại",
        defaults={"slug": "uncategorized", "is_hidden": True},
    )
    return category


@staff_required
def project_create(request):
    categories = ProjectCategory.objects.filter(is_hidden=False).order_by("name")

    if request.method == 'POST':
        category_id = request.POST.get("category")
        category = None
        if category_id:
            category = ProjectCategory.objects.filter(id=category_id).first()
        if category is None:
            category = _get_default_project_category()

        Project.objects.create(
            name=request.POST.get('name'),
            description=request.POST.get('description'),
            image=request.FILES.get('image'),
            category=category,
        )
        return redirect('dashboard')

    return render(request, 'home/project_form.html', {"categories": categories})


@staff_required
def project_update(request, id):
    project = get_object_or_404(Project, id=id)
    categories = ProjectCategory.objects.filter(is_hidden=False).order_by("name")

    if request.method == 'POST':
        project.name = request.POST.get('name')
        project.description = request.POST.get('description')

        category_id = request.POST.get("category")
        if category_id:
            category = ProjectCategory.objects.filter(id=category_id).first()
            if category is not None:
                project.category = category

        if 'image' in request.FILES:
            project.image = request.FILES['image']
        project.save() 
        return redirect('dashboard')

    return render(
        request,
        'home/project_form.html',
        {'project': project, "categories": categories},
    )


@staff_required
def project_delete(request, id):
    project = get_object_or_404(Project, id=id)
    project.delete()
    return redirect('dashboard')


# ====================== AUTH ======================
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect("dashboard")
        return redirect("home")

    next_url = request.GET.get('next') or request.POST.get('next')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            next_path = None
            if next_url:
                next_path = urlparse(next_url).path

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ) and ((user.is_staff or user.is_superuser) or not _is_management_path(next_path)):
                return redirect(next_url)

            if user.is_staff or user.is_superuser:
                return redirect("home")
            return redirect("home")
    else:
        form = LoginForm(request)
    return render(request, 'accounts/login.html', {
        'form': form,
        'next': next_url,
    })

def register_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect("dashboard")
        return redirect("home")

    next_url = request.GET.get("next") or request.POST.get("next")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Đăng ký thành công.")

            next_path = None
            if next_url:
                next_path = urlparse(next_url).path

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ) and not _is_management_path(next_path):
                return redirect(next_url)
            return redirect("home")
    else:
        form = UserRegistrationForm()

    return render(request, "accounts/register.html", {"form": form, "next": next_url})


def logout_view(request):
    if not request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        logout(request)
        return redirect("home")

    return render(request, "accounts/logout.html")

@staff_required
def dashboard(request):
    projects = Project.objects.all().order_by('-id')
    products = Product.objects.all().order_by("-id")
    return render(request, 'home/dashboard.html', {'projects': projects, "products": products})


# ====================== CRUD PRODUCT ======================
@staff_required
def product_list(request):
    products = Product.objects.select_related("category").all().order_by("-id")
    return render(request, "home/product_list.html", {"products": products})


def product_public(request):
    categories = ProductCategory.objects.filter(is_hidden=False).order_by("name")
    products = Product.objects.select_related("category").all().order_by("-created_at", "-id")
    return render(
        request,
        "home/product.html",
        {"products": products, "categories": categories},
    )


def product_detail(request, id):
    product = get_object_or_404(Product.objects.select_related("category"), id=id)
    return render(request, "home/product_detail.html", {"product": product})


@staff_required
def product_create(request):
    categories = ProductCategory.objects.filter(is_hidden=False).order_by("name")

    if request.method == "POST":
        category_id = request.POST.get("category")
        category = None
        if category_id:
            category = ProductCategory.objects.filter(id=category_id).first()
        if category is None:
            category = _get_default_product_category()

        Product.objects.create(
            name=request.POST.get("name"),
            description=request.POST.get("description", ""),
            image=request.FILES.get("image"),
            category=category,
        )
        return redirect("product_list")

    return render(request, "home/product_form.html", {"categories": categories})


@staff_required
def product_update(request, id):
    product = get_object_or_404(Product, id=id)
    categories = ProductCategory.objects.filter(is_hidden=False).order_by("name")

    if request.method == "POST":
        product.name = request.POST.get("name")
        product.description = request.POST.get("description", "")

        category_id = request.POST.get("category")
        if category_id:
            category = ProductCategory.objects.filter(id=category_id).first()
            if category is not None:
                product.category = category

        if "image" in request.FILES:
            product.image = request.FILES["image"]

        product.save()
        return redirect("product_list")

    return render(
        request,
        "home/product_form.html",
        {"product": product, "categories": categories},
    )


@staff_required
def product_delete(request, id):
    product = get_object_or_404(Product, id=id)
    product.delete()
    return redirect("product_list")


# ====================== CRUD CATEGORIES ======================
@staff_required
def project_category_list(request):
    categories = ProjectCategory.objects.all().order_by("name")
    error = request.GET.get("error")
    return render(
        request,
        "home/project_category_list.html",
        {"categories": categories, "error": error},
    )


@staff_required
def project_category_create(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        slug = (request.POST.get("slug") or "").strip() or None
        is_hidden = request.POST.get("is_hidden") == "on"

        if not slug and name:
            slug = slugify(name) or None

        if name:
            ProjectCategory.objects.create(name=name, slug=slug, is_hidden=is_hidden)
            return redirect("project_category_list")

    return render(request, "home/project_category_form.html", {"title": "Thêm danh mục dự án"})


@staff_required
def project_category_update(request, id):
    category = get_object_or_404(ProjectCategory, id=id)

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        slug = (request.POST.get("slug") or "").strip() or None
        is_hidden = request.POST.get("is_hidden") == "on"

        if not slug and name:
            slug = slugify(name) or None

        category.name = name or category.name
        category.slug = slug
        category.is_hidden = is_hidden
        category.save()
        return redirect("project_category_list")

    return render(
        request,
        "home/project_category_form.html",
        {"title": "Sửa danh mục dự án", "category": category},
    )


@staff_required
def project_category_delete(request, id):
    category = get_object_or_404(ProjectCategory, id=id)
    try:
        category.delete()
    except ProtectedError:
        return redirect("project_category_list" + "?error=Không thể xóa danh mục đang được sử dụng.")
    return redirect("project_category_list")


@staff_required
def product_category_list(request):
    categories = ProductCategory.objects.all().order_by("name")
    error = request.GET.get("error")
    return render(
        request,
        "home/product_category_list.html",
        {"categories": categories, "error": error},
    )


@staff_required
def product_category_create(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        slug = (request.POST.get("slug") or "").strip() or None
        is_hidden = request.POST.get("is_hidden") == "on"

        if not slug and name:
            slug = slugify(name) or None

        if name:
            ProductCategory.objects.create(name=name, slug=slug, is_hidden=is_hidden)
            return redirect("product_category_list")

    return render(request, "home/product_category_form.html", {"title": "Thêm danh mục sản phẩm"})


@staff_required
def product_category_update(request, id):
    category = get_object_or_404(ProductCategory, id=id)

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        slug = (request.POST.get("slug") or "").strip() or None
        is_hidden = request.POST.get("is_hidden") == "on"

        if not slug and name:
            slug = slugify(name) or None

        category.name = name or category.name
        category.slug = slug
        category.is_hidden = is_hidden
        category.save()
        return redirect("product_category_list")

    return render(
        request,
        "home/product_category_form.html",
        {"title": "Sửa danh mục sản phẩm", "category": category},
    )


@staff_required
def product_category_delete(request, id):
    category = get_object_or_404(ProductCategory, id=id)
    try:
        category.delete()
    except ProtectedError:
        return redirect("product_category_list" + "?error=Không thể xóa danh mục đang được sử dụng.")
    return redirect("product_category_list")
