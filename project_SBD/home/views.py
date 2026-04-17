# views.py
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models.deletion import ProtectedError
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
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
    Consultation,
    Notification,
    AboutIntro
)

User = get_user_model()

CONSULTATION_PROJECT_TYPES = Consultation.PROJECT_TYPE_CHOICES

CONSULTATION_BUDGET_CHOICES = [
    "Dưới 1 tỷ VNĐ",
    "1 – 5 tỷ VNĐ",
    "5 – 20 tỷ VNĐ",
    "20 – 100 tỷ VNĐ",
    "Trên 100 tỷ VNĐ",
]

CONSULTATION_STATUS_LABELS = dict(Consultation.STATUS_CHOICES)


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


def _get_staff_recipients():
    return User.objects.filter(is_active=True).filter(
        is_staff=True
    ) | User.objects.filter(is_active=True, is_superuser=True)


def _create_notification(user, message, notification_type, consultation=None, link=""):
    return Notification.objects.create(
        user=user,
        message=message,
        notification_type=notification_type,
        consultation=consultation,
        link=link or "",
    )


def _notify_new_consultation(consultation):
    consultation_link = reverse("consultation_detail", args=[consultation.id])
    recipients = _get_staff_recipients().exclude(id=consultation.user_id).distinct()

    for recipient in recipients:
        _create_notification(
            user=recipient,
            message=(
                f"Có yêu cầu tư vấn mới từ {consultation.full_name} - "
                f"{consultation.subject}"
            ),
            notification_type="consult",
            consultation=consultation,
            link=consultation_link,
        )


def _notify_consultation_status_change(consultation):
    status_text = CONSULTATION_STATUS_LABELS.get(consultation.status, consultation.status)
    handled_by = consultation.handled_by.username if consultation.handled_by else "nhân viên"
    _create_notification(
        user=consultation.user,
        message=(
            f"Yêu cầu tư vấn '{consultation.subject}' của bạn đã được cập nhật "
            f"sang trạng thái {status_text} bởi {handled_by}."
        ),
        notification_type="answer",
        consultation=consultation,
        link=reverse("contact"),
    )


# ====================== PUBLIC PAGES ======================
def home(request):
    projects = Project.objects.filter(is_featured=True)

    return render(request, 'home/home.html', {
        'projects': projects
    })


def about(request):
    leadership_members = LeadershipMember.objects.filter(is_active=True).order_by("order", "created_at")
    vision_statements = AboutStatement.objects.filter(statement_type="vision", is_active=True).order_by("order", "created_at")
    mission_statements = AboutStatement.objects.filter(statement_type="mission", is_active=True).order_by("order", "created_at")

    all_certs = list(Certificate.objects.filter(is_active=True).order_by("order", "created_at"))
    mid = (len(all_certs) + 1) // 2
    certs_left = all_certs[:mid]
    certs_right = all_certs[mid:]
    intro = AboutIntro.objects.first()

    return render(request, "home/about.html", {
        "leadership_members": leadership_members,
        "vision_statements": vision_statements,
        "mission_statements": mission_statements,
        "certs_left": certs_left,
        "certs_right": certs_right,
        "intro": intro,
    })


def contact(request):
    faqs = FAQ.objects.filter(is_active=True).order_by("order", "created_at")
    contact_infos = ContactInfo.objects.filter(is_active=True).order_by(
        "order", "created_at"
    )
    main_contact = contact_infos.first()
    user_consultations = Consultation.objects.none()

    if request.user.is_authenticated:
        user_consultations = Consultation.objects.filter(user=request.user).select_related(
            "handled_by"
        )

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.warning(
                request,
                "Bạn cần đăng nhập để gửi yêu cầu tư vấn và nhận thông báo xử lý.",
            )
            return redirect(f"{reverse('login')}?next={request.path}")

        full_name = (request.POST.get("name") or "").strip()
        phone = (request.POST.get("phone") or "").strip()
        email = (request.POST.get("email") or "").strip()
        project_type = (request.POST.get("project_type") or "").strip()
        subject = (request.POST.get("subject") or "").strip()
        content = (request.POST.get("message") or "").strip()
        budget = (request.POST.get("budget") or "").strip()
        valid_project_types = {value for value, _ in CONSULTATION_PROJECT_TYPES}

        if not all([full_name, phone, project_type, subject]):
            messages.error(request, "Vui lòng nhập đầy đủ các trường bắt buộc.")
        elif project_type not in valid_project_types:
            messages.error(request, "Loại dự án không hợp lệ.")
        else:
            consultation = Consultation.objects.create(
                user=request.user,
                full_name=full_name,
                phone=phone,
                email=email,
                project_type=project_type,
                subject=subject,
                budget=budget,
                content=content,
            )
            _notify_new_consultation(consultation)
            messages.success(
                request,
                "Đã gửi yêu cầu tư vấn thành công. Bạn sẽ nhận được thông báo khi yêu cầu được xử lý.",
            )
            return redirect("contact")

    return render(
        request,
        "home/contact.html",
        {
            "faqs": faqs,
            "contact_infos": contact_infos,
            "main_contact": main_contact,
            "project_type_choices": CONSULTATION_PROJECT_TYPES,
            "budget_choices": CONSULTATION_BUDGET_CHOICES,
            "user_consultations": user_consultations,
            "status_labels": CONSULTATION_STATUS_LABELS,
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
    consultations_pending = Consultation.objects.filter(status="pending").count()
    consultations_processing = Consultation.objects.filter(status="processing").count()
    return render(
        request,
        "home/dashboard.html",
        {
            "projects": projects,
            "products": products,
            "consultations_pending": consultations_pending,
            "consultations_processing": consultations_processing,
        },
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
        order = request.POST.get("order") or 0
        is_active = request.POST.get("is_active") == "on"

        if title and description:
            Certificate.objects.create(
                title=title,
                description=description,
                icon=icon,
                order=int(order),
                is_active=is_active,
                image=request.FILES.get("image"),
            )
            return redirect("certificate_list")

    return render(request, "home/about_certificate_form.html", {
        "title": "Thêm chứng chỉ mới",
        "icon_choices": Certificate.ICON_CHOICES,
    })


@staff_required
def certificate_update(request, id):
    cert = get_object_or_404(Certificate, id=id)

    if request.method == "POST":
        cert.title = (request.POST.get("title") or "").strip() or cert.title
        cert.description = (request.POST.get("description") or "").strip() or cert.description
        cert.icon = request.POST.get("icon") or cert.icon
        cert.order = int(request.POST.get("order") or 0)
        cert.is_active = request.POST.get("is_active") == "on"
        if "image" in request.FILES:
            cert.image = request.FILES["image"]
        cert.save()
        return redirect("certificate_list")

    return render(request, "home/about_certificate_form.html", {
        "title": "Sửa chứng chỉ",
        "cert": cert,
        "icon_choices": Certificate.ICON_CHOICES,
    })


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
        branch_name = request.POST.get("branch_name", "").strip()
        address = request.POST.get("address", "").strip()
        phone = request.POST.get("phone", "").strip()
        fax = request.POST.get("fax", "").strip()
        email = request.POST.get("email", "").strip()
        working_hours = request.POST.get("working_hours", "").strip()
        map_embed_url = request.POST.get("map_embed_url", "").strip()
        facebook_url = request.POST.get("facebook_url", "").strip()
        youtube_url = request.POST.get("youtube_url", "").strip()
        linkedin_url = request.POST.get("linkedin_url", "").strip()
        instagram_url = request.POST.get("instagram_url", "").strip()
        order = request.POST.get("order", 0)

        posted_is_active = request.POST.get("is_active")
        if posted_is_active is None:
            is_active = True
        else:
            is_active = posted_is_active == "on"

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
            order=order or 0,
            is_active=is_active,
        )

        messages.success(request, "Thêm thông tin liên hệ thành công.")
        return redirect("contact_info_list")

    return render(request, "home/contact_info_form.html")


@staff_required
def contact_info_update(request, pk):
    contact_info = get_object_or_404(ContactInfo, pk=pk)

    if request.method == "POST":
        contact_info.branch_name = request.POST.get("branch_name", "").strip()
        contact_info.address = request.POST.get("address", "").strip()
        contact_info.phone = request.POST.get("phone", "").strip()
        contact_info.fax = request.POST.get("fax", "").strip()
        contact_info.email = request.POST.get("email", "").strip()
        contact_info.working_hours = request.POST.get("working_hours", "").strip()
        contact_info.map_embed_url = request.POST.get("map_embed_url", "").strip()
        contact_info.facebook_url = request.POST.get("facebook_url", "").strip()
        contact_info.youtube_url = request.POST.get("youtube_url", "").strip()
        contact_info.linkedin_url = request.POST.get("linkedin_url", "").strip()
        contact_info.instagram_url = request.POST.get("instagram_url", "").strip()
        contact_info.order = request.POST.get("order", 0) or 0

        posted_is_active = request.POST.get("is_active")
        if posted_is_active is not None:
            contact_info.is_active = posted_is_active == "on"

        contact_info.save()
        messages.success(request, "Cập nhật thông tin liên hệ thành công.")
        return redirect("contact_info_list")

    return render(
        request,
        "home/contact_info_form.html",
        {"contact_info": contact_info},
    )


@staff_required
def contact_info_delete(request, id):
    contact_info = get_object_or_404(ContactInfo, id=id)
    contact_info.delete()
    return redirect("contact_info_list")


@staff_required
def contact_info_toggle_status(request, pk):
    contact_info = get_object_or_404(ContactInfo, pk=pk)

    if request.method == "POST":
        contact_info.is_active = not contact_info.is_active
        contact_info.save()

        if contact_info.is_active:
            messages.success(request, f"Đã hiển thị: {contact_info.branch_name}")
        else:
            messages.success(request, f"Đã ẩn: {contact_info.branch_name}")

    return redirect("contact_info_list")


@staff_required
def consultation_list(request):
    consultations = Consultation.objects.select_related("user", "handled_by").all()
    status_filter = (request.GET.get("status") or "").strip()

    if status_filter in CONSULTATION_STATUS_LABELS:
        consultations = consultations.filter(status=status_filter)

    return render(
        request,
        "home/consultation_list.html",
        {
            "consultations": consultations,
            "status_filter": status_filter,
            "status_choices": Consultation.STATUS_CHOICES,
        },
    )


@staff_required
def consultation_detail(request, id):
    consultation = get_object_or_404(
        Consultation.objects.select_related("user", "handled_by"),
        id=id,
    )

    if request.method == "POST":
        new_status = (request.POST.get("status") or "").strip()
        valid_statuses = {value for value, _ in Consultation.STATUS_CHOICES}

        if new_status not in valid_statuses:
            messages.error(request, "Trạng thái không hợp lệ.")
        else:
            status_changed = consultation.status != new_status
            consultation.status = new_status
            consultation.handled_by = request.user
            consultation.save()

            Notification.objects.filter(
                consultation=consultation,
                user=request.user,
                notification_type="consult",
                is_read=False,
            ).update(is_read=True)

            if status_changed:
                _notify_consultation_status_change(consultation)
                messages.success(request, "Đã cập nhật trạng thái yêu cầu tư vấn.")
            else:
                messages.success(request, "Đã cập nhật người xử lý yêu cầu tư vấn.")

            return redirect("consultation_detail", id=consultation.id)

    return render(
        request,
        "home/consultation_detail.html",
        {
            "consultation": consultation,
            "status_choices": Consultation.STATUS_CHOICES,
        },
    )


@login_required
def notifications(request):
    user_notifications = request.user.notifications.select_related("consultation")
    return render(
        request,
        "home/notifications.html",
        {"notifications": user_notifications},
    )


@login_required
def notification_read(request, id):
    notification = get_object_or_404(
        Notification.objects.select_related("consultation"),
        id=id,
        user=request.user,
    )
    notification.is_read = True
    notification.save(update_fields=["is_read"])

    if notification.link:
        return redirect(notification.link)

    if notification.consultation_id:
        if request.user.is_staff or request.user.is_superuser:
            return redirect("consultation_detail", id=notification.consultation_id)
        return redirect("contact")

    return redirect("notifications")


@login_required
def notification_mark_all_read(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return redirect("notifications")

# ====================== CRUD ABOUT INTRO ======================
@staff_required
def about_intro_edit(request):
    intro = AboutIntro.objects.first()

    if request.method == "POST":
        data = request.POST
        if intro is None:
            intro = AboutIntro()

        intro.kicker = data.get("kicker", "").strip()
        intro.brand_name = data.get("brand_name", "").strip()
        intro.slogan = data.get("slogan", "").strip()
        intro.highlight_1 = data.get("highlight_1", "").strip()
        intro.highlight_2 = data.get("highlight_2", "").strip()
        intro.highlight_3 = data.get("highlight_3", "").strip()
        intro.badge_number = data.get("badge_number", "").strip()
        intro.badge_text = data.get("badge_text", "").strip()
        intro.heading = data.get("heading", "").strip()
        intro.paragraph_1 = data.get("paragraph_1", "").strip()
        intro.paragraph_2 = data.get("paragraph_2", "").strip()
        intro.bullet_points = data.get("bullet_points", "").strip()
        intro.save()
        messages.success(request, "Đã cập nhật phần giới thiệu!")
        return redirect("about_intro_edit")

    return render(request, "home/about_intro_form.html", {"intro": intro})