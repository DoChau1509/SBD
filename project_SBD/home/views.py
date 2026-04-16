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
    Post,
    PostCategory,
    FAQ,
    LeadershipMember,
    AboutStatement,
    Certificate,
    ContactInfo,
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
        "/posts",
        "/post/add",
        "/post/edit",
        "/post/delete",
        "/post-category",
        "/leadership",
        "/about-statements",
        "/contact-infos",
        "/contact-info/add",
        "/contact-info/edit",
        "/contact-info/delete",
    )
    return path.startswith(management_prefixes)


# ====================== PUBLIC PAGES ======================
def home(request):
    return render(request, "home/home.html")


def about(request):
    leadership_members = LeadershipMember.objects.filter(is_active=True).order_by(
        "order", "created_at"
    )
    vision_statements = AboutStatement.objects.filter(
        statement_type="vision", is_active=True
    ).order_by("order", "created_at")
    mission_statements = AboutStatement.objects.filter(
        statement_type="mission", is_active=True
    ).order_by("order", "created_at")
    certs_left = Certificate.objects.filter(is_active=True, side="left").order_by(
        "order"
    )
    certs_right = Certificate.objects.filter(is_active=True, side="right").order_by(
        "order"
    )

    return render(
        request,
        "home/about.html",
        {
            "leadership_members": leadership_members,
            "vision_statements": vision_statements,
            "mission_statements": mission_statements,
            "certs_left": certs_left,
            "certs_right": certs_right,
        },
    )


def contact(request):
    faqs = FAQ.objects.filter(is_active=True).order_by("order", "created_at")
    contact_infos = ContactInfo.objects.filter(is_active=True).order_by(
        "order", "created_at"
    )
    main_contact = contact_infos.first()

    return render(
        request,
        "home/contact.html",
        {
            "faqs": faqs,
            "contact_infos": contact_infos,
            "main_contact": main_contact,
        },
    )


def project(request):
    categories = ProjectCategory.objects.filter(is_hidden=False).order_by("name")
    projects = (
        Project.objects.select_related("category").all().order_by("-created_at", "-id")
    )
    return render(
        request,
        "home/project.html",
        {"projects": projects, "categories": categories},
    )


def project_detail(request, id):
    project = get_object_or_404(Project, id=id)
    return render(request, "home/project_detail.html", {"project": project})


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


def _get_default_post_category():
    category, _ = PostCategory.objects.get_or_create(
        name="Chưa phân loại",
        defaults={"slug": "uncategorized-post", "is_hidden": True},
    )
    return category


@staff_required
def project_create(request):
    categories = ProjectCategory.objects.filter(is_hidden=False).order_by("name")

    if request.method == "POST":
        category_id = request.POST.get("category")
        category = None
        if category_id:
            category = ProjectCategory.objects.filter(id=category_id).first()
        if category is None:
            category = _get_default_project_category()

        Project.objects.create(
            name=request.POST.get("name"),
            description=request.POST.get("description"),
            image=request.FILES.get("image"),
            category=category,
        )
        return redirect("dashboard")

    return render(request, "home/project_form.html", {"categories": categories})


@staff_required
def project_update(request, id):
    project = get_object_or_404(Project, id=id)
    categories = ProjectCategory.objects.filter(is_hidden=False).order_by("name")

    if request.method == "POST":
        project.name = request.POST.get("name")
        project.description = request.POST.get("description")

        category_id = request.POST.get("category")
        if category_id:
            category = ProjectCategory.objects.filter(id=category_id).first()
            if category is not None:
                project.category = category

        if "image" in request.FILES:
            project.image = request.FILES["image"]
        project.save()
        return redirect("dashboard")

    return render(
        request,
        "home/project_form.html",
        {"project": project, "categories": categories},
    )


@staff_required
def project_delete(request, id):
    project = get_object_or_404(Project, id=id)
    project.delete()
    return redirect("dashboard")


# ====================== AUTH ======================
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect("dashboard")
        return redirect("home")

    next_url = request.GET.get("next") or request.POST.get("next")
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            next_path = None
            if next_url:
                next_path = urlparse(next_url).path

            if (
                next_url
                and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                )
                and (
                    (user.is_staff or user.is_superuser)
                    or not _is_management_path(next_path)
                )
            ):
                return redirect(next_url)

            if user.is_staff or user.is_superuser:
                return redirect("home")
            return redirect("home")
    else:
        form = LoginForm(request)
    return render(
        request,
        "accounts/login.html",
        {
            "form": form,
            "next": next_url,
        },
    )


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

            if (
                next_url
                and url_has_allowed_host_and_scheme(
                    next_url,
                    allowed_hosts={request.get_host()},
                    require_https=request.is_secure(),
                )
                and not _is_management_path(next_path)
            ):
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
    projects = Project.objects.all().order_by("-id")
    products = Product.objects.all().order_by("-id")
    return render(
        request, "home/dashboard.html", {"projects": projects, "products": products}
    )


# ====================== CRUD PRODUCT ======================
@staff_required
def product_list(request):
    products = Product.objects.select_related("category").all().order_by("-id")
    return render(request, "home/product_list.html", {"products": products})


def product_public(request):
    categories = ProductCategory.objects.filter(is_hidden=False).order_by("name")
    products = (
        Product.objects.select_related("category").all().order_by("-created_at", "-id")
    )
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


# ====================== CRUD POST ======================
@staff_required
def post_list(request):
    posts = Post.objects.select_related("category").all().order_by("-id")
    return render(request, "home/post_list.html", {"posts": posts})


def post_public(request):
    categories = PostCategory.objects.filter(is_hidden=False).order_by("name")
    posts = Post.objects.select_related("category").all().order_by("-created_at", "-id")
    return render(
        request,
        "home/post.html",
        {"posts": posts, "categories": categories},
    )


def post_detail(request, id):
    post = get_object_or_404(Post.objects.select_related("category"), id=id)
    return render(request, "home/post_detail.html", {"post": post})


@staff_required
def post_create(request):
    categories = PostCategory.objects.filter(is_hidden=False).order_by("name")

    if request.method == "POST":
        category_id = request.POST.get("category")
        category = None
        if category_id:
            category = PostCategory.objects.filter(id=category_id).first()
        if category is None:
            category = _get_default_post_category()

        Post.objects.create(
            title=request.POST.get("title"),
            summary=request.POST.get("summary", ""),
            content=request.POST.get("content"),
            image=request.FILES.get("image"),
            category=category,
        )
        return redirect("post_list")

    return render(request, "home/post_form.html", {"categories": categories})


@staff_required
def post_update(request, id):
    post = get_object_or_404(Post, id=id)
    categories = PostCategory.objects.filter(is_hidden=False).order_by("name")

    if request.method == "POST":
        post.title = request.POST.get("title")
        post.summary = request.POST.get("summary", "")
        post.content = request.POST.get("content")

        category_id = request.POST.get("category")
        if category_id:
            category = PostCategory.objects.filter(id=category_id).first()
            if category is not None:
                post.category = category

        if "image" in request.FILES:
            post.image = request.FILES["image"]

        post.save()
        return redirect("post_list")

    return render(
        request,
        "home/post_form.html",
        {"post": post, "categories": categories},
    )


@staff_required
def post_delete(request, id):
    post = get_object_or_404(Post, id=id)
    post.delete()
    return redirect("post_list")


@staff_required
def post_category_list(request):
    categories = PostCategory.objects.all().order_by("name")
    error = request.GET.get("error")
    return render(
        request,
        "home/post_category_list.html",
        {"categories": categories, "error": error},
    )


@staff_required
def post_category_create(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        slug = (request.POST.get("slug") or "").strip() or None
        is_hidden = request.POST.get("is_hidden") == "on"

        if not slug and name:
            slug = slugify(name) or None

        if name:
            PostCategory.objects.create(name=name, slug=slug, is_hidden=is_hidden)
            return redirect("post_category_list")

    return render(
        request, "home/post_category_form.html", {"title": "Thêm danh mục bài viết"}
    )


@staff_required
def post_category_update(request, id):
    category = get_object_or_404(PostCategory, id=id)

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
        return redirect("post_category_list")

    return render(
        request,
        "home/post_category_form.html",
        {"title": "Sửa danh mục bài viết", "category": category},
    )


@staff_required
def post_category_delete(request, id):
    category = get_object_or_404(PostCategory, id=id)
    try:
        category.delete()
    except ProtectedError:
        return redirect(
            "post_category_list" + "?error=Không thể xóa danh mục đang được sử dụng."
        )
    return redirect("post_category_list")


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

    return render(
        request, "home/project_category_form.html", {"title": "Thêm danh mục dự án"}
    )


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
        return redirect(
            "project_category_list" + "?error=Không thể xóa danh mục đang được sử dụng."
        )
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

    return render(
        request, "home/product_category_form.html", {"title": "Thêm danh mục sản phẩm"}
    )


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
        return redirect(
            "product_category_list" + "?error=Không thể xóa danh mục đang được sử dụng."
        )
    return redirect("product_category_list")


# ====================== CRUD FAQ ======================
@staff_required
def faq_list(request):
    faqs = FAQ.objects.all()
    error = request.GET.get("error")
    return render(request, "home/faq_list.html", {"faqs": faqs, "error": error})


@staff_required
def faq_create(request):
    if request.method == "POST":
        question = (request.POST.get("question") or "").strip()
        answer = (request.POST.get("answer") or "").strip()
        order = request.POST.get("order") or 0
        is_active = request.POST.get("is_active") == "on"

        if question and answer:
            FAQ.objects.create(
                question=question,
                answer=answer,
                order=int(order),
                is_active=is_active,
            )
            return redirect("faq_list")

    return render(request, "home/faq_form.html", {"title": "Thêm câu hỏi mới"})


@staff_required
def faq_update(request, id):
    faq = get_object_or_404(FAQ, id=id)

    if request.method == "POST":
        question = (request.POST.get("question") or "").strip()
        answer = (request.POST.get("answer") or "").strip()
        order = request.POST.get("order") or 0
        is_active = request.POST.get("is_active") == "on"

        faq.question = question or faq.question
        faq.answer = answer or faq.answer
        faq.order = int(order)
        faq.is_active = is_active
        faq.save()
        return redirect("faq_list")

    return render(request, "home/faq_form.html", {"title": "Sửa câu hỏi", "faq": faq})


@staff_required
def faq_delete(request, id):
    faq = get_object_or_404(FAQ, id=id)
    faq.delete()
    return redirect("faq_list")


##############################
# ====================== CRUD LEADERSHIP ======================
@staff_required
def leadership_list(request):
    leadership_members = LeadershipMember.objects.all().order_by("order", "created_at")
    error = request.GET.get("error")
    return render(
        request,
        "home/leadership_list.html",
        {"leadership_members": leadership_members, "error": error},
    )


@staff_required
def leadership_create(request):
    if request.method == "POST":
        full_name = (request.POST.get("full_name") or "").strip()
        role = (request.POST.get("role") or "").strip()
        bio = (request.POST.get("bio") or "").strip()
        initials = (request.POST.get("initials") or "").strip()
        linkedin_url = (request.POST.get("linkedin_url") or "").strip()
        facebook_url = (request.POST.get("facebook_url") or "").strip()
        instagram_url = (request.POST.get("instagram_url") or "").strip()
        order = request.POST.get("order") or 0
        is_active = request.POST.get("is_active") == "on"
        image = request.FILES.get("image")

        if full_name and role and bio:
            LeadershipMember.objects.create(
                full_name=full_name,
                role=role,
                bio=bio,
                image=image,
                initials=initials,
                linkedin_url=linkedin_url,
                facebook_url=facebook_url,
                instagram_url=instagram_url,
                order=int(order),
                is_active=is_active,
            )
            return redirect("leadership_list")

    return render(
        request, "home/leadership_form.html", {"title": "Thêm thành viên ban lãnh đạo"}
    )


@staff_required
def leadership_update(request, id):
    leadership_member = get_object_or_404(LeadershipMember, id=id)

    if request.method == "POST":
        full_name = (request.POST.get("full_name") or "").strip()
        role = (request.POST.get("role") or "").strip()
        bio = (request.POST.get("bio") or "").strip()
        initials = (request.POST.get("initials") or "").strip()
        linkedin_url = (request.POST.get("linkedin_url") or "").strip()
        facebook_url = (request.POST.get("facebook_url") or "").strip()
        instagram_url = (request.POST.get("instagram_url") or "").strip()
        order = request.POST.get("order") or 0
        is_active = request.POST.get("is_active") == "on"

        leadership_member.full_name = full_name or leadership_member.full_name
        leadership_member.role = role or leadership_member.role
        leadership_member.bio = bio or leadership_member.bio
        leadership_member.initials = initials
        leadership_member.linkedin_url = linkedin_url
        leadership_member.facebook_url = facebook_url
        leadership_member.instagram_url = instagram_url
        leadership_member.order = int(order)
        leadership_member.is_active = is_active

        if "image" in request.FILES:
            leadership_member.image = request.FILES["image"]

        leadership_member.save()
        return redirect("leadership_list")

    return render(
        request,
        "home/leadership_form.html",
        {
            "title": "Sửa thành viên ban lãnh đạo",
            "leadership_member": leadership_member,
        },
    )


@staff_required
def leadership_delete(request, id):
    leadership_member = get_object_or_404(LeadershipMember, id=id)
    leadership_member.delete()
    return redirect("leadership_list")


# ====================== CRUD ABOUT STATEMENTS ======================
@staff_required
def statement_list(request):
    statements = AboutStatement.objects.all().order_by(
        "statement_type", "order", "created_at"
    )
    error = request.GET.get("error")
    return render(
        request,
        "home/about_statement_list.html",
        {"statements": statements, "error": error},
    )


@staff_required
def statement_create(request):
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        statement_type = (request.POST.get("statement_type") or "").strip()
        content = (request.POST.get("content") or "").strip()
        icon = (request.POST.get("icon") or "fa-star").strip()
        order = request.POST.get("order") or 0
        is_active = request.POST.get("is_active") == "on"

        if title and statement_type in {"vision", "mission"} and content:
            AboutStatement.objects.create(
                title=title,
                statement_type=statement_type,
                content=content,
                icon=icon or "fa-star",
                order=int(order),
                is_active=is_active,
            )
            return redirect("statement_list")

    return render(
        request, "home/about_statement_form.html", {"title": "Thêm tầm nhìn / sứ mệnh"}
    )


@staff_required
def statement_update(request, id):
    statement = get_object_or_404(AboutStatement, id=id)

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        statement_type = (request.POST.get("statement_type") or "").strip()
        content = (request.POST.get("content") or "").strip()
        icon = (request.POST.get("icon") or "fa-star").strip()
        order = request.POST.get("order") or 0
        is_active = request.POST.get("is_active") == "on"

        if statement_type not in {"vision", "mission"}:
            statement_type = statement.statement_type

        statement.title = title or statement.title
        statement.statement_type = statement_type
        statement.content = content or statement.content
        statement.icon = icon or "fa-star"
        statement.order = int(order)
        statement.is_active = is_active
        statement.save()
        return redirect("statement_list")

    return render(
        request,
        "home/about_statement_form.html",
        {"title": "Sửa tầm nhìn / sứ mệnh", "statement": statement},
    )


@staff_required
def statement_delete(request, id):
    statement = get_object_or_404(AboutStatement, id=id)
    statement.delete()
    return redirect("statement_list")


# ====================== CRUD CERTIFICATE ======================
@staff_required
def certificate_list(request):
    certs = Certificate.objects.all()
    return render(request, "home/about_certificate_list.html", {"certs": certs})


@staff_required
def certificate_create(request):
    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        description = (request.POST.get("description") or "").strip()
        icon = request.POST.get("icon") or "fa-certificate"
        side = request.POST.get("side") or "left"
        order = request.POST.get("order") or 0
        is_active = request.POST.get("is_active") == "on"

        if title and description:
            Certificate.objects.create(
                title=title,
                description=description,
                icon=icon,
                side=side,
                order=int(order),
                is_active=is_active,
                image=request.FILES.get("image"),
            )
            return redirect("certificate_list")

    return render(
        request,
        "home/about_certificate_form.html",
        {
            "title": "Thêm chứng chỉ mới",
            "icon_choices": Certificate.ICON_CHOICES,
            "side_choices": Certificate.SIDE_CHOICES,
        },
    )


@staff_required
def certificate_update(request, id):
    cert = get_object_or_404(Certificate, id=id)

    if request.method == "POST":
        cert.title = (request.POST.get("title") or "").strip() or cert.title
        cert.description = (
            request.POST.get("description") or ""
        ).strip() or cert.description
        cert.icon = request.POST.get("icon") or cert.icon
        cert.side = request.POST.get("side") or cert.side
        cert.order = int(request.POST.get("order") or 0)
        cert.is_active = request.POST.get("is_active") == "on"
        if "image" in request.FILES:
            cert.image = request.FILES["image"]
        cert.save()
        return redirect("certificate_list")

    return render(
        request,
        "home/about_certificate_form.html",
        {
            "title": "Sửa chứng chỉ",
            "cert": cert,
            "icon_choices": Certificate.ICON_CHOICES,
            "side_choices": Certificate.SIDE_CHOICES,
        },
    )


@staff_required
def certificate_delete(request, id):
    cert = get_object_or_404(Certificate, id=id)
    cert.delete()
    return redirect("certificate_list")


# ====================== CRUD CONTACT INFO ======================
@staff_required
def contact_info_list(request):
    contact_infos = ContactInfo.objects.all().order_by("order", "created_at")
    return render(
        request, "home/contact_info_list.html", {"contact_infos": contact_infos}
    )


@staff_required
def contact_info_create(request):
    if request.method == "POST":
        branch_name = (request.POST.get("branch_name") or "").strip()
        address = (request.POST.get("address") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        fax = (request.POST.get("fax") or "").strip()
        email = (request.POST.get("email") or "").strip()
        working_hours = (request.POST.get("working_hours") or "").strip()
        map_embed_url = (request.POST.get("map_embed_url") or "").strip()
        facebook_url = (request.POST.get("facebook_url") or "").strip()
        youtube_url = (request.POST.get("youtube_url") or "").strip()
        linkedin_url = (request.POST.get("linkedin_url") or "").strip()
        instagram_url = (request.POST.get("instagram_url") or "").strip()
        order = int(request.POST.get("order") or 0)
        is_active = request.POST.get("is_active") == "on"

        if branch_name and address and phone:
            ContactInfo.objects.create(
                branch_name=branch_name,
                address=address,
                phone=phone,
                fax=fax,
                email=email,
                working_hours=working_hours,
                map_embed_url=map_embed_url,
                facebook_url=facebook_url,
                youtube_url=youtube_url,
                linkedin_url=linkedin_url,
                instagram_url=instagram_url,
                order=order,
                is_active=is_active,
            )
            return redirect("contact_info_list")

    return render(
        request, "home/contact_info_form.html", {"title": "Thêm thông tin liên lạc"}
    )


@staff_required
def contact_info_update(request, id):
    contact_info = get_object_or_404(ContactInfo, id=id)

    if request.method == "POST":
        contact_info.branch_name = (
            request.POST.get("branch_name") or ""
        ).strip() or contact_info.branch_name
        contact_info.address = (
            request.POST.get("address") or ""
        ).strip() or contact_info.address
        contact_info.phone = (
            request.POST.get("phone") or ""
        ).strip() or contact_info.phone
        contact_info.fax = (request.POST.get("fax") or "").strip()
        contact_info.email = (request.POST.get("email") or "").strip()
        contact_info.working_hours = (request.POST.get("working_hours") or "").strip()
        contact_info.map_embed_url = (request.POST.get("map_embed_url") or "").strip()
        contact_info.facebook_url = (request.POST.get("facebook_url") or "").strip()
        contact_info.youtube_url = (request.POST.get("youtube_url") or "").strip()
        contact_info.linkedin_url = (request.POST.get("linkedin_url") or "").strip()
        contact_info.instagram_url = (request.POST.get("instagram_url") or "").strip()
        contact_info.order = int(request.POST.get("order") or 0)
        contact_info.is_active = request.POST.get("is_active") == "on"
        contact_info.save()
        return redirect("contact_info_list")

    return render(
        request,
        "home/contact_info_form.html",
        {
            "title": "Sửa thông tin liên lạc",
            "contact_info": contact_info,
        },
    )


@staff_required
def contact_info_delete(request, id):
    contact_info = get_object_or_404(ContactInfo, id=id)
    contact_info.delete()
    return redirect("contact_info_list")
