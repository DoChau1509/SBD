# views.py
import json
import random
import unicodedata
from datetime import timedelta
from functools import wraps
from urllib.parse import urlparse

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.text import slugify
from django.utils.http import url_has_allowed_host_and_scheme
from .forms import (
    UserRegistrationForm,
    LoginForm,
    StaffAccountCreationForm,
    StaffAccountUpdateForm,
    ForgotPasswordRequestForm,
    OTPPasswordResetForm,
    ChangePasswordRequestForm,
    EmailOTPSettingsForm,
    SiteBrandSettingsForm,
)
from .models import (
    Product,
    ProductCategory,
    Project,
    ProjectCategory,
    Post,
    PostCategory,
    FAQ,
    LeadershipMember,
    AboutStatementType,
    AboutStatement,
    ServiceType,
    Service,
    Certificate,
    ContactInfo,
    Consultation,
    Notification,
    AboutIntro,
    HomeWhyChooseSection,
    HomeWhyChooseItem,
    HeroSection,
    HeroCarouselImage,
    AboutVideoTour,
    Partner,
    EmailOTPSettings,
    PasswordOTP,
    SiteBrandSettings,
    OfficeRental,
    EducationSpaceDesign,
    SpecializedServiceContent,
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
CONSULTATION_STATUS_ORDER = {
    status: index for index, (status, _) in enumerate(Consultation.STATUS_CHOICES)
}

SPECIALIZED_SERVICE_SECTORS = {
    SpecializedServiceContent.INDUSTRIAL: {
        "title": "Công Nghiệp",
        "description": "Giải pháp thiết kế và xây dựng công trình công nghiệp hiệu quả, an toàn và bền vững",
        "icon": "fa-solid fa-industry",
        "public_url_name": "industrial",
        "detail_url_name": "industrial_detail",
        "list_url_name": "industrial_list",
        "add_url_name": "industrial_add",
        "edit_url_name": "industrial_edit",
        "delete_url_name": "industrial_delete",
    },
    SpecializedServiceContent.CIVIL: {
        "title": "Dân Dụng",
        "description": "Giải pháp thiết kế và xây dựng công trình dân dụng tiện nghi, thẩm mỹ và bền vững",
        "icon": "fa-solid fa-house",
        "public_url_name": "civil",
        "detail_url_name": "civil_detail",
        "list_url_name": "civil_list",
        "add_url_name": "civil_add",
        "edit_url_name": "civil_edit",
        "delete_url_name": "civil_delete",
    },
    SpecializedServiceContent.ENERGY_GREEN: {
        "title": "Năng Lượng Và Công Trình Xanh",
        "description": "Giải pháp năng lượng hiệu quả và công trình xanh thân thiện với môi trường",
        "icon": "fa-solid fa-leaf",
        "public_url_name": "energy_green",
        "detail_url_name": "energy_green_detail",
        "list_url_name": "energy_green_list",
        "add_url_name": "energy_green_add",
        "edit_url_name": "energy_green_edit",
        "delete_url_name": "energy_green_delete",
    },
    SpecializedServiceContent.INTERIOR_COMMERCIAL: {
        "title": "Nội Thất Và Thương Mại",
        "description": "Giải pháp thiết kế nội thất và không gian thương mại tối ưu công năng, trải nghiệm và nhận diện",
        "icon": "fa-solid fa-couch",
        "public_url_name": "interior_commercial",
        "detail_url_name": "interior_commercial_detail",
        "list_url_name": "interior_commercial_list",
        "add_url_name": "interior_commercial_add",
        "edit_url_name": "interior_commercial_edit",
        "delete_url_name": "interior_commercial_delete",
    },
}


def _get_specialized_service_config(sector):
    config = SPECIALIZED_SERVICE_SECTORS.get(sector)
    if config is None:
        raise ValueError(f"Unsupported specialized service sector: {sector}")
    return config


MANAGEMENT_SEARCH_ACTIONS = [
    {
        "title": "Quản lý dự án",
        "description": "Xem, sửa và xóa các dự án.",
        "url_name": "dashboard",
        "icon": "fa-solid fa-building",
        "keywords": "du an cong trinh project",
    },
    {
        "title": "Thêm dự án",
        "description": "Tạo một dự án mới.",
        "url_name": "project_add",
        "icon": "fa-solid fa-plus",
        "keywords": "du an cong trinh tao moi",
    },
    {
        "title": "Dự án nổi bật",
        "description": "Chọn các dự án hiển thị nổi bật trên trang chủ.",
        "url_name": "featured_project_list",
        "icon": "fa-solid fa-star",
        "keywords": "du an noi bat trang chu",
    },
    {
        "title": "Danh mục dự án",
        "description": "Quản lý các danh mục dự án.",
        "url_name": "project_category_list",
        "icon": "fa-solid fa-folder-tree",
        "keywords": "danh muc loai du an",
    },
    {
        "title": "Quản lý sản phẩm",
        "description": "Xem, thêm, sửa và xóa sản phẩm.",
        "url_name": "product_list",
        "icon": "fa-solid fa-box-open",
        "keywords": "san pham product hang hoa",
    },
    {
        "title": "Thêm sản phẩm",
        "description": "Tạo một sản phẩm mới.",
        "url_name": "product_add",
        "icon": "fa-solid fa-plus",
        "keywords": "san pham tao moi",
    },
    {
        "title": "Danh mục sản phẩm",
        "description": "Quản lý các danh mục sản phẩm.",
        "url_name": "product_category_list",
        "icon": "fa-solid fa-folder-tree",
        "keywords": "danh muc loai san pham",
    },
    {
        "title": "Quản lý bài viết",
        "description": "Xem, thêm, sửa và xóa bài viết.",
        "url_name": "post_list",
        "icon": "fa-solid fa-newspaper",
        "keywords": "bai viet tin tuc post",
    },
    {
        "title": "Thêm bài viết",
        "description": "Tạo một bài viết mới.",
        "url_name": "post_add",
        "icon": "fa-solid fa-plus",
        "keywords": "bai viet tin tuc tao moi",
    },
    {
        "title": "Danh mục bài viết",
        "description": "Quản lý các danh mục bài viết.",
        "url_name": "post_category_list",
        "icon": "fa-solid fa-folder-tree",
        "keywords": "danh muc loai bai viet tin tuc",
    },
    {
        "title": "Quản lý dịch vụ",
        "description": "Quản lý nội dung dịch vụ trên trang chủ.",
        "url_name": "service_list",
        "icon": "fa-solid fa-screwdriver-wrench",
        "keywords": "dich vu trang chu service",
    },
    {
        "title": "Loại dịch vụ",
        "description": "Quản lý các loại dịch vụ.",
        "url_name": "service_type_list",
        "icon": "fa-solid fa-list",
        "keywords": "danh muc loai dich vu",
    },
    {
        "title": "Cho thuê văn phòng",
        "description": "Quản lý nội dung văn phòng cho thuê.",
        "url_name": "office_rental_list",
        "icon": "fa-solid fa-briefcase",
        "keywords": "van phong cho thue office rental",
    },
    {
        "title": "Thiết kế không gian giáo dục",
        "description": "Quản lý nội dung dịch vụ không gian giáo dục.",
        "url_name": "education_space_design_list",
        "icon": "fa-solid fa-school",
        "keywords": "giao duc truong hoc khong gian",
    },
    {
        "title": "Dịch vụ công nghiệp",
        "description": "Quản lý nội dung dịch vụ công nghiệp.",
        "url_name": "industrial_list",
        "icon": "fa-solid fa-industry",
        "keywords": "cong nghiep nha may industrial",
    },
    {
        "title": "Dịch vụ dân dụng",
        "description": "Quản lý nội dung dịch vụ dân dụng.",
        "url_name": "civil_list",
        "icon": "fa-solid fa-house",
        "keywords": "dan dung nha o civil",
    },
    {
        "title": "Năng lượng và công trình xanh",
        "description": "Quản lý nội dung năng lượng và công trình xanh.",
        "url_name": "energy_green_list",
        "icon": "fa-solid fa-leaf",
        "keywords": "nang luong cong trinh xanh moi truong",
    },
    {
        "title": "Nội thất và thương mại",
        "description": "Quản lý nội dung nội thất và thương mại.",
        "url_name": "interior_commercial_list",
        "icon": "fa-solid fa-couch",
        "keywords": "noi that thuong mai commercial",
    },
    {
        "title": "Hero trang chủ",
        "description": "Chỉnh sửa hình ảnh và nội dung Hero.",
        "url_name": "hero_edit",
        "icon": "fa-solid fa-images",
        "keywords": "hero banner trang chu slide carousel",
    },
    {
        "title": "Tại sao chọn chúng tôi",
        "description": "Quản lý các lý do và nội dung nổi bật.",
        "url_name": "why_choose_item_list",
        "icon": "fa-solid fa-circle-check",
        "keywords": "tai sao chon chung toi ly do",
    },
    {
        "title": "Đối tác",
        "description": "Quản lý logo và thông tin đối tác.",
        "url_name": "partner_list",
        "icon": "fa-solid fa-handshake",
        "keywords": "doi tac partner logo",
    },
    {
        "title": "Giới thiệu công ty",
        "description": "Chỉnh sửa phần giới thiệu công ty.",
        "url_name": "about_intro_edit",
        "icon": "fa-solid fa-circle-info",
        "keywords": "gioi thieu cong ty about",
    },
    {
        "title": "Tầm nhìn và sứ mệnh",
        "description": "Quản lý nội dung tầm nhìn và sứ mệnh.",
        "url_name": "statement_list",
        "icon": "fa-solid fa-eye",
        "keywords": "tam nhin su menh gia tri",
    },
    {
        "title": "Quy trình giới thiệu",
        "description": "Chỉnh sửa quy trình triển khai trên trang giới thiệu.",
        "url_name": "about_video_tour_edit",
        "icon": "fa-solid fa-list-check",
        "keywords": "quy trinh gioi thieu video tour",
    },
    {
        "title": "Ban lãnh đạo",
        "description": "Quản lý thông tin thành viên ban lãnh đạo.",
        "url_name": "leadership_list",
        "icon": "fa-solid fa-user-tie",
        "keywords": "ban lanh dao nhan su thanh vien",
    },
    {
        "title": "Chứng chỉ",
        "description": "Quản lý chứng chỉ và thành tựu.",
        "url_name": "certificate_list",
        "icon": "fa-solid fa-certificate",
        "keywords": "chung chi thanh tuu certificate",
    },
    {
        "title": "Thông tin liên hệ",
        "description": "Quản lý địa chỉ, số điện thoại và mạng xã hội.",
        "url_name": "contact_info_list",
        "icon": "fa-solid fa-address-book",
        "keywords": "lien he dia chi dien thoai email contact",
    },
    {
        "title": "Câu hỏi thường gặp",
        "description": "Quản lý danh sách câu hỏi và câu trả lời.",
        "url_name": "faq_list",
        "icon": "fa-solid fa-circle-question",
        "keywords": "faq cau hoi thuong gap",
    },
    {
        "title": "Yêu cầu tư vấn",
        "description": "Xem và xử lý yêu cầu tư vấn của khách hàng.",
        "url_name": "consultation_list",
        "icon": "fa-solid fa-comments",
        "keywords": "tu van yeu cau khach hang consultation",
    },
    {
        "title": "Cài đặt hệ thống",
        "description": "Quản lý thương hiệu, email OTP và tài khoản staff.",
        "url_name": "system_settings",
        "icon": "fa-solid fa-gear",
        "keywords": "cai dat he thong logo email otp staff",
        "admin_only": True,
    },
    {
        "title": "Icon tab trình duyệt",
        "description": "Thay ảnh favicon xuất hiện cạnh tiêu đề trên tab trình duyệt.",
        "url_name": "system_settings",
        "url_fragment": "favicon-settings",
        "icon": "fa-solid fa-window-maximize",
        "keywords": "favicon icon dau trang tab trinh duyet base hinh anh",
        "admin_only": True,
    },
    {
        "title": "Tạo tài khoản staff",
        "description": "Tạo tài khoản nhân viên quản trị mới.",
        "url_name": "staff_account_add",
        "icon": "fa-solid fa-user-plus",
        "keywords": "tao tai khoan staff nhan vien admin",
        "admin_only": True,
    },
]


def _normalize_search_text(value):
    normalized = unicodedata.normalize("NFD", (value or "").lower())
    return "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Mn"
    ).replace("đ", "d")


def _search_management_actions(user, query):
    if not query or not user.is_authenticated or not (
        user.is_staff or user.is_superuser
    ):
        return []

    normalized_query = _normalize_search_text(query)
    results = []

    for action in MANAGEMENT_SEARCH_ACTIONS:
        if action.get("admin_only") and not user.is_superuser:
            continue

        searchable_text = " ".join(
            [
                action["title"],
                action["description"],
                action.get("keywords", ""),
            ]
        )
        if normalized_query not in _normalize_search_text(searchable_text):
            continue

        url = reverse(action["url_name"])
        if action.get("url_fragment"):
            url = f"{url}#{action['url_fragment']}"
        results.append({**action, "url": url})

    return results[:12]


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


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/login/?next={request.path}")

        if request.user.is_superuser:
            return view_func(request, *args, **kwargs)

        messages.warning(request, "Chỉ quản trị viên mới có quyền quản lý tài khoản.")
        return redirect("dashboard")

    return _wrapped


def _is_management_path(path: str) -> bool:
    if not path:
        return False

    management_prefixes = (
        "/dashboard",
        "/project/add",
        "/project/edit",
        "/project/delete",
        "/project/featured",
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
        "/office-rentals",
        "/office-rental/add",
        "/office-rental/edit",
        "/office-rental/delete",
        "/education-space-designs",
        "/education-space-design/add",
        "/education-space-design/edit",
        "/education-space-design/delete",
        "/industrial-services",
        "/industrial/add",
        "/industrial/edit",
        "/industrial/delete",
        "/civil-services",
        "/civil/add",
        "/civil/edit",
        "/civil/delete",
        "/energy-green-services",
        "/energy-green/add",
        "/energy-green/edit",
        "/energy-green/delete",
        "/interior-commercial-services",
        "/interior-commercial/add",
        "/interior-commercial/edit",
        "/interior-commercial/delete",
        "/leadership",
        "/about-statements",
        "/service-types",
        "/services",
        "/contact-infos",
        "/contact-info/add",
        "/contact-info/edit",
        "/contact-info/delete",
        "/partners",
        "/partner/add",
        "/partner/edit",
        "/partner/delete",
        "/staff-accounts",
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
    status_text = CONSULTATION_STATUS_LABELS.get(
        consultation.status, consultation.status
    )
    handled_by = (
        consultation.handled_by.username if consultation.handled_by else "nhân viên"
    )
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


def _can_move_consultation_status(current_status, new_status):
    current_index = CONSULTATION_STATUS_ORDER.get(current_status, -1)
    new_index = CONSULTATION_STATUS_ORDER.get(new_status, -1)
    return new_index >= current_index


def _mask_email(email):
    email = (email or "").strip()
    if not email or "@" not in email:
        return ""
    local_part, domain = email.split("@", 1)
    if len(local_part) <= 2:
        masked_local = local_part[:1] + "*"
    else:
        masked_local = local_part[:2] + "*" * max(len(local_part) - 2, 1)
    return f"{masked_local}@{domain}"


def _get_email_otp_settings():
    return EmailOTPSettings.get_solo()


def _build_email_connection(config):
    backend = getattr(
        settings,
        "EMAIL_BACKEND",
        "django.core.mail.backends.smtp.EmailBackend",
    )
    return get_connection(
        backend=backend,
        host=config.smtp_host,
        port=config.smtp_port,
        username=config.smtp_username or "",
        password=config.smtp_password or "",
        use_tls=config.use_tls,
        use_ssl=config.use_ssl,
        fail_silently=False,
    )


def _generate_otp_code():
    return f"{random.SystemRandom().randint(0, 999999):06d}"


def _send_password_otp_email(user, otp):
    config = _get_email_otp_settings()

    if not config.sender_email or not config.smtp_host:
        raise ValueError("Chưa cấu hình email gửi OTP.")

    purpose_text = dict(PasswordOTP.PURPOSE_CHOICES).get(otp.purpose, "Xác minh")
    subject = f"[Sao Bac Dau] Ma OTP {purpose_text.lower()}"
    body = (
        f"Xin chao {user.get_full_name() or user.username},\n\n"
        f"Ma OTP cua ban la: {otp.code}\n"
        f"Ma co hieu luc den {timezone.localtime(otp.expires_at).strftime('%H:%M:%S %d/%m/%Y')}.\n"
        "Neu ban khong thuc hien yeu cau nay, vui long bo qua email nay.\n\n"
        "Sao Bac Dau Construction"
    )

    email_message = EmailMultiAlternatives(
        subject=subject,
        body=body,
        from_email=config.from_email,
        to=[otp.email],
        connection=_build_email_connection(config),
    )
    email_message.send(fail_silently=False)


def _issue_password_otp(user, purpose):
    email = (user.email or "").strip().lower()
    if not email:
        raise ValueError("Tài khoản này chưa có email để nhận OTP.")

    PasswordOTP.objects.filter(
        user=user,
        purpose=purpose,
        is_used=False,
    ).update(is_used=True)

    otp = PasswordOTP.objects.create(
        user=user,
        email=email,
        purpose=purpose,
        code=_generate_otp_code(),
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    _send_password_otp_email(user, otp)
    return otp


def _get_active_otp(user, purpose, code):
    return (
        PasswordOTP.objects.filter(
            user=user,
            purpose=purpose,
            code=(code or "").strip(),
            is_used=False,
            expires_at__gt=timezone.now(),
        )
        .order_by("-created_at")
        .first()
    )


# ====================== PUBLIC PAGES ======================
# def home(request):
#     projects = Project.objects.filter(is_featured=True)
#     services = (
#         Service.objects.filter(is_active=True, service_type__is_active=True)
#         .select_related("service_type")
#         .order_by(
#             "service_type__order",
#             "service_type__created_at",
#             "order",
#             "created_at",
#         )
#     )


#     return render(
#         request,
#         "home/home.html",
#         {
#             "projects": projects,
#             "services": services,
#         },
#     )
def home(request):
    hero = HeroSection.objects.filter(is_active=True).first()
    projects = Project.objects.filter(is_featured=True)
    partners = Partner.objects.filter(is_active=True).order_by("order", "created_at")
    services = (
        Service.objects.filter(is_active=True, service_type__is_active=True)
        .select_related("service_type")
        .order_by(
            "service_type__order",
            "service_type__created_at",
            "order",
            "created_at",
        )
    )

    why_section = HomeWhyChooseSection.objects.first()
    why_items = HomeWhyChooseItem.objects.filter(is_active=True).order_by(
        "order", "created_at"
    )

    return render(
        request,
        "home/home.html",
        {
            "projects": projects,
            "services": services,
            "why_section": why_section,
            "why_items": why_items,
            "hero": hero,
            "partners": partners,
        },
    )


def about(request):
    leadership_members = LeadershipMember.objects.filter(is_active=True).order_by(
        "order", "created_at"
    )

    about_statements = (
        AboutStatement.objects.filter(is_active=True, statement_type__is_active=True)
        .select_related("statement_type")
        .order_by(
            "statement_type__order",
            "statement_type__created_at",
            "order",
            "created_at",
        )
    )

    all_certs = list(
        Certificate.objects.filter(is_active=True).order_by("order", "created_at")
    )
    mid = (len(all_certs) + 1) // 2
    certs_left = all_certs[:mid]
    certs_right = all_certs[mid:]
    intro = AboutIntro.objects.first()
    about_video_tour = AboutVideoTour.objects.first()

    return render(
        request,
        "home/about.html",
        {
            "leadership_members": leadership_members,
            "about_statements": about_statements,
            "certs_left": certs_left,
            "certs_right": certs_right,
            "intro": intro,
            "about_video_tour": about_video_tour,
        },
    )


def contact(request):
    faqs = FAQ.objects.filter(is_active=True).order_by("order", "created_at")
    contact_infos = ContactInfo.objects.filter(is_active=True).order_by(
        "order", "created_at"
    )
    main_contact = contact_infos.first()
    user_consultations = Consultation.objects.none()

    if request.user.is_authenticated:
        user_consultations = Consultation.objects.filter(
            user=request.user
        ).select_related("handled_by")

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


def search(request):
    query = (request.GET.get("q") or "").strip()

    projects = []
    products = []
    posts = []
    office_rentals = []
    education_space_designs = []
    specialized_service_contents = []
    management_actions = []

    if query:
        management_actions = _search_management_actions(request.user, query)
        projects = list(
            Project.objects.select_related("category")
            .filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(category__name__icontains=query)
            )
            .distinct()
            .order_by("-created_at", "-id")[:8]
        )
        products = list(
            Product.objects.select_related("category")
            .filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(supplier_name__icontains=query)
                | Q(supplier_address__icontains=query)
                | Q(category__name__icontains=query)
            )
            .distinct()
            .order_by("-created_at", "-id")[:8]
        )
        posts = list(
            Post.objects.select_related("category")
            .filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(content__icontains=query)
                | Q(category__name__icontains=query)
            )
            .distinct()
            .order_by("-created_at", "-id")[:8]
        )
        office_rentals = list(
            OfficeRental.objects.filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(content__icontains=query)
            )
            .distinct()
            .order_by("-created_at", "-id")[:8]
        )
        education_space_designs = list(
            EducationSpaceDesign.objects.filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(content__icontains=query)
            )
            .distinct()
            .order_by("-created_at", "-id")[:8]
        )
        specialized_service_contents = list(
            SpecializedServiceContent.objects.filter(
                Q(title__icontains=query)
                | Q(summary__icontains=query)
                | Q(content__icontains=query)
            )
            .distinct()
            .order_by("-created_at", "-id")[:12]
        )

    result_count = (
        len(projects)
        + len(products)
        + len(posts)
        + len(office_rentals)
        + len(education_space_designs)
        + len(specialized_service_contents)
        + len(management_actions)
    )

    return render(
        request,
        "home/search_results.html",
        {
            "query": query,
            "projects": projects,
            "products": products,
            "posts": posts,
            "office_rentals": office_rentals,
            "education_space_designs": education_space_designs,
            "specialized_service_contents": specialized_service_contents,
            "management_actions": management_actions,
            "result_count": result_count,
        },
    )


def project(request):
    query = (request.GET.get("q") or "").strip()
    categories = ProjectCategory.objects.filter(is_hidden=False).order_by("name")
    projects = (
        Project.objects.select_related("category").all().order_by("-created_at", "-id")
    )

    if query:
        projects = projects.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        ).distinct()

    return render(
        request,
        "home/project.html",
        {"projects": projects, "categories": categories, "query": query},
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


@staff_required
def featured_project_list(request):
    projects = Project.objects.select_related("category").all().order_by("-created_at", "-id")

    if request.method == "POST":
        featured_ids = {
            int(project_id)
            for project_id in request.POST.getlist("featured_projects")
            if project_id.isdigit()
        }
        Project.objects.exclude(id__in=featured_ids).update(is_featured=False)
        Project.objects.filter(id__in=featured_ids).update(is_featured=True)
        messages.success(request, "Đã cập nhật danh sách dự án nổi bật.")
        return redirect("featured_project_list")

    return render(
        request,
        "home/featured_project_list.html",
        {"projects": projects},
    )


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


def forgot_password_request(request):
    if request.user.is_authenticated:
        return redirect("change_password_request")

    if request.method == "POST":
        form = ForgotPasswordRequestForm(request.POST)
        if form.is_valid():
            identifier = (form.cleaned_data["identifier"] or "").strip()
            user = User.objects.filter(username__iexact=identifier).first()
            if user is None:
                user = User.objects.filter(email__iexact=identifier).first()

            request.session.pop("forgot_password_user_id", None)
            request.session.pop("forgot_password_masked_email", None)

            if user and user.email:
                try:
                    _issue_password_otp(user, "forgot_password")
                    request.session["forgot_password_user_id"] = user.id
                    request.session["forgot_password_masked_email"] = _mask_email(
                        user.email
                    )
                except Exception:
                    messages.error(
                        request,
                        "Không thể gửi OTP lúc này. Vui lòng kiểm tra cấu hình email hoặc thử lại sau.",
                    )
                    return redirect("forgot_password")

            messages.success(
                request,
                "Nếu tài khoản hợp lệ, mã OTP đã được gửi tới email đã đăng ký.",
            )
            return redirect("forgot_password_verify")
    else:
        form = ForgotPasswordRequestForm()

    return render(request, "accounts/forgot_password_request.html", {"form": form})


def forgot_password_verify(request):
    user_id = request.session.get("forgot_password_user_id")
    masked_email = request.session.get("forgot_password_masked_email", "")

    if not user_id:
        messages.warning(request, "Bạn cần gửi yêu cầu OTP trước.")
        return redirect("forgot_password")

    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = OTPPasswordResetForm(request.POST, user=user)
        if form.is_valid():
            otp = _get_active_otp(
                user,
                "forgot_password",
                form.cleaned_data["otp_code"],
            )
            if otp is None:
                form.add_error("otp_code", "Mã OTP không đúng hoặc đã hết hạn.")
            else:
                user.set_password(form.cleaned_data["password1"])
                user.save(update_fields=["password"])
                otp.is_used = True
                otp.save(update_fields=["is_used"])
                request.session.pop("forgot_password_user_id", None)
                request.session.pop("forgot_password_masked_email", None)
                messages.success(request, "Đặt lại mật khẩu thành công. Hãy đăng nhập lại.")
                return redirect("login")
    else:
        form = OTPPasswordResetForm(user=user)

    return render(
        request,
        "accounts/forgot_password_verify.html",
        {
            "form": form,
            "masked_email": masked_email,
            "page_title": "Xác nhận OTP để đặt lại mật khẩu",
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


@login_required
def change_password_request(request):
    if not request.user.email:
        messages.warning(
            request,
            "Tài khoản của bạn chưa có email. Vui lòng liên hệ admin để cập nhật email trước khi đổi mật khẩu bằng OTP.",
        )
        return redirect("home")

    if request.method == "POST":
        form = ChangePasswordRequestForm(request.POST, user=request.user)
        if form.is_valid():
            try:
                _issue_password_otp(request.user, "change_password")
                request.session["change_password_user_id"] = request.user.id
                request.session["change_password_masked_email"] = _mask_email(
                    request.user.email
                )
                messages.success(
                    request,
                    "Mã OTP đã được gửi tới email của bạn.",
                )
                return redirect("change_password_verify")
            except Exception:
                messages.error(
                    request,
                    "Không thể gửi OTP lúc này. Vui lòng kiểm tra cấu hình email hoặc thử lại sau.",
                )
    else:
        form = ChangePasswordRequestForm(user=request.user)

    return render(request, "accounts/change_password_request.html", {"form": form})


@login_required
def change_password_verify(request):
    user_id = request.session.get("change_password_user_id")
    masked_email = request.session.get("change_password_masked_email", "")

    if user_id != request.user.id:
        messages.warning(request, "Bạn cần yêu cầu OTP đổi mật khẩu trước.")
        return redirect("change_password_request")

    if request.method == "POST":
        form = OTPPasswordResetForm(request.POST, user=request.user)
        if form.is_valid():
            otp = _get_active_otp(
                request.user,
                "change_password",
                form.cleaned_data["otp_code"],
            )
            if otp is None:
                form.add_error("otp_code", "Mã OTP không đúng hoặc đã hết hạn.")
            else:
                request.user.set_password(form.cleaned_data["password1"])
                request.user.save(update_fields=["password"])
                otp.is_used = True
                otp.save(update_fields=["is_used"])
                request.session.pop("change_password_user_id", None)
                request.session.pop("change_password_masked_email", None)
                logout(request)
                messages.success(
                    request,
                    "Đổi mật khẩu thành công. Vui lòng đăng nhập lại bằng mật khẩu mới.",
                )
                return redirect("login")
    else:
        form = OTPPasswordResetForm(user=request.user)

    return render(
        request,
        "accounts/change_password_verify.html",
        {
            "form": form,
            "masked_email": masked_email,
        },
    )


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


@admin_required
def system_settings(request):
    config = _get_email_otp_settings()
    brand_config = SiteBrandSettings.get_solo()
    staff_accounts = User.objects.filter(is_staff=True, is_superuser=False).order_by(
        "-is_active", "username"
    )

    if request.method == "POST":
        form_type = (request.POST.get("form_type") or "").strip()

        if form_type == "email_settings":
            form = EmailOTPSettingsForm(request.POST, instance=config)
            brand_form = SiteBrandSettingsForm(instance=brand_config)
            if form.is_valid():
                form.save()
                messages.success(request, "Đã cập nhật cấu hình email gửi OTP.")
                return redirect("system_settings")
        elif form_type == "brand_settings":
            brand_form = SiteBrandSettingsForm(
                request.POST,
                request.FILES,
                instance=brand_config,
            )
            form = EmailOTPSettingsForm(instance=config)
            if brand_form.is_valid():
                brand_form.save()
                messages.success(request, "Đã cập nhật thành công.")
                return redirect("system_settings")
        else:
            form = EmailOTPSettingsForm(instance=config)
            brand_form = SiteBrandSettingsForm(instance=brand_config)
    else:
        form = EmailOTPSettingsForm(instance=config)
        brand_form = SiteBrandSettingsForm(instance=brand_config)

    return render(
        request,
        "home/system_settings.html",
        {
            "form": form,
            "brand_form": brand_form,
            "brand_config": brand_config,
            "config": config,
            "staff_accounts": staff_accounts,
        },
    )


@admin_required
def email_otp_settings_edit(request):
    return redirect("system_settings")


@admin_required
def staff_account_list(request):
    return redirect("system_settings")


@admin_required
def staff_account_create(request):
    if request.method == "POST":
        form = StaffAccountCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã tạo tài khoản staff mới.")
            return redirect("staff_account_list")
    else:
        form = StaffAccountCreationForm()

    return render(
        request,
        "home/staff_account_form.html",
        {
            "form": form,
            "page_title": "Tạo tài khoản staff",
            "submit_label": "Tạo tài khoản",
            "back_url": reverse("system_settings"),
        },
    )


@admin_required
def staff_account_update(request, id):
    staff_account = get_object_or_404(
        User,
        id=id,
        is_staff=True,
        is_superuser=False,
    )

    if request.method == "POST":
        form = StaffAccountUpdateForm(request.POST, instance=staff_account)
        if form.is_valid():
            form.save()
            messages.success(request, "Đã cập nhật tài khoản staff.")
            return redirect("staff_account_list")
    else:
        form = StaffAccountUpdateForm(instance=staff_account)

    return render(
        request,
        "home/staff_account_form.html",
        {
            "form": form,
            "page_title": "Cập nhật tài khoản staff",
            "submit_label": "Lưu thay đổi",
            "staff_account": staff_account,
            "back_url": reverse("system_settings"),
        },
    )


@admin_required
def staff_account_toggle_status(request, id):
    staff_account = get_object_or_404(
        User,
        id=id,
        is_staff=True,
        is_superuser=False,
    )

    if request.method == "POST":
        staff_account.is_active = not staff_account.is_active
        staff_account.save(update_fields=["is_active"])
        if staff_account.is_active:
            messages.success(
                request,
                f"Đã kích hoạt lại tài khoản {staff_account.username}.",
            )
        else:
            messages.success(
                request,
                f"Đã khóa tài khoản {staff_account.username}.",
            )

    return redirect("staff_account_list")


# ====================== CRUD PRODUCT ======================
@staff_required
def product_list(request):
    products = Product.objects.select_related("category").all().order_by("-id")
    return render(request, "home/product_list.html", {"products": products})


def product_public(request):
    query = (request.GET.get("q") or "").strip()
    categories = ProductCategory.objects.filter(is_hidden=False).order_by("name")
    products = (
        Product.objects.select_related("category").all().order_by("-created_at", "-id")
    )

    if query:
        products = products.filter(
            Q(name__icontains=query)
            | Q(description__icontains=query)
            | Q(supplier_name__icontains=query)
            | Q(supplier_address__icontains=query)
            | Q(category__name__icontains=query)
        ).distinct()

    return render(
        request,
        "home/product.html",
        {"products": products, "categories": categories, "query": query},
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
            supplier_name=request.POST.get("supplier_name", "").strip(),
            supplier_address=request.POST.get("supplier_address", "").strip(),
            supplier_map_embed_url=request.POST.get(
                "supplier_map_embed_url", ""
            ).strip(),
            category=category,
        )
        return redirect("product_list")

    return render(request, "home/product_form.html", {"categories": categories})


@staff_required
def product_update(request, id):
    product = get_object_or_404(Product, id=id)
    categories = ProductCategory.objects.filter(is_hidden=False).order_by("name")

    if request.method == "POST":
        # product.name = request.POST.get("name")
        # product.description = request.POST.get("description", "")
        product.name = request.POST.get("name")
        product.description = request.POST.get("description", "")
        product.supplier_name = request.POST.get("supplier_name", "").strip()
        product.supplier_address = request.POST.get("supplier_address", "").strip()
        product.supplier_map_embed_url = request.POST.get(
            "supplier_map_embed_url", ""
        ).strip()

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


def office_rental_public(request):
    query = (request.GET.get("q") or "").strip()
    office_rentals = OfficeRental.objects.all().order_by("-created_at", "-id")

    if query:
        office_rentals = office_rentals.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(content__icontains=query)
        ).distinct()

    return render(
        request,
        "home/office_rental.html",
        {"office_rentals": office_rentals, "query": query},
    )


def office_rental_detail(request, id):
    office_rental = get_object_or_404(OfficeRental, id=id)
    return render(
        request,
        "home/office_rental_detail.html",
        {"office_rental": office_rental},
    )


def education_space_design_public(request):
    query = (request.GET.get("q") or "").strip()
    education_space_designs = EducationSpaceDesign.objects.all().order_by(
        "-created_at", "-id"
    )

    if query:
        education_space_designs = education_space_designs.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(content__icontains=query)
        ).distinct()

    return render(
        request,
        "home/education_space_design.html",
        {"education_space_designs": education_space_designs, "query": query},
    )


def education_space_design_detail(request, id):
    education_space_design = get_object_or_404(EducationSpaceDesign, id=id)
    return render(
        request,
        "home/education_space_design_detail.html",
        {"education_space_design": education_space_design},
    )


def specialized_service_public(request, sector):
    config = _get_specialized_service_config(sector)
    query = (request.GET.get("q") or "").strip()
    items = SpecializedServiceContent.objects.filter(sector=sector)

    if query:
        items = items.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(content__icontains=query)
        ).distinct()

    return render(
        request,
        "home/specialized_service.html",
        {"items": items, "query": query, "service_config": config},
    )


def specialized_service_detail(request, id, sector):
    config = _get_specialized_service_config(sector)
    item = get_object_or_404(SpecializedServiceContent, id=id, sector=sector)
    return render(
        request,
        "home/specialized_service_detail.html",
        {"item": item, "service_config": config},
    )


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
def office_rental_list(request):
    office_rentals = OfficeRental.objects.all().order_by("-id")
    return render(
        request,
        "home/office_rental_list.html",
        {"office_rentals": office_rentals},
    )


@staff_required
def office_rental_create(request):
    if request.method == "POST":
        OfficeRental.objects.create(
            title=request.POST.get("title"),
            summary=request.POST.get("summary", ""),
            content=request.POST.get("content"),
            image=request.FILES.get("image"),
            area=request.POST.get("area") or 0,
            rent_price=request.POST.get("rent_price") or 0,
        )
        return redirect("office_rental_list")

    return render(request, "home/office_rental_form.html")


@staff_required
def office_rental_update(request, id):
    office_rental = get_object_or_404(OfficeRental, id=id)

    if request.method == "POST":
        office_rental.title = request.POST.get("title")
        office_rental.summary = request.POST.get("summary", "")
        office_rental.content = request.POST.get("content")
        office_rental.area = request.POST.get("area") or 0
        office_rental.rent_price = request.POST.get("rent_price") or 0

        if "image" in request.FILES:
            office_rental.image = request.FILES["image"]

        office_rental.save()
        return redirect("office_rental_list")

    return render(
        request,
        "home/office_rental_form.html",
        {"office_rental": office_rental},
    )


@staff_required
def office_rental_delete(request, id):
    office_rental = get_object_or_404(OfficeRental, id=id)
    office_rental.delete()
    return redirect("office_rental_list")


@staff_required
def education_space_design_list(request):
    education_space_designs = EducationSpaceDesign.objects.all().order_by("-id")
    return render(
        request,
        "home/education_space_design_list.html",
        {"education_space_designs": education_space_designs},
    )


@staff_required
def education_space_design_create(request):
    if request.method == "POST":
        EducationSpaceDesign.objects.create(
            title=request.POST.get("title"),
            summary=request.POST.get("summary", ""),
            content=request.POST.get("content"),
            image=request.FILES.get("image"),
        )
        return redirect("education_space_design_list")

    return render(request, "home/education_space_design_form.html")


@staff_required
def education_space_design_update(request, id):
    education_space_design = get_object_or_404(EducationSpaceDesign, id=id)

    if request.method == "POST":
        education_space_design.title = request.POST.get("title")
        education_space_design.summary = request.POST.get("summary", "")
        education_space_design.content = request.POST.get("content")

        if "image" in request.FILES:
            education_space_design.image = request.FILES["image"]

        education_space_design.save()
        return redirect("education_space_design_list")

    return render(
        request,
        "home/education_space_design_form.html",
        {"education_space_design": education_space_design},
    )


@staff_required
def education_space_design_delete(request, id):
    education_space_design = get_object_or_404(EducationSpaceDesign, id=id)
    education_space_design.delete()
    return redirect("education_space_design_list")


@staff_required
def specialized_service_list(request, sector):
    config = _get_specialized_service_config(sector)
    items = SpecializedServiceContent.objects.filter(sector=sector).order_by("-id")
    return render(
        request,
        "home/specialized_service_list.html",
        {
            "items": items,
            "service_config": config,
            "service_sectors": SPECIALIZED_SERVICE_SECTORS.values(),
        },
    )


@staff_required
def specialized_service_create(request, sector):
    config = _get_specialized_service_config(sector)

    if request.method == "POST":
        SpecializedServiceContent.objects.create(
            sector=sector,
            title=request.POST.get("title"),
            summary=request.POST.get("summary", ""),
            content=request.POST.get("content"),
            image=request.FILES.get("image"),
        )
        return redirect(config["list_url_name"])

    return render(
        request,
        "home/specialized_service_form.html",
        {"service_config": config},
    )


@staff_required
def specialized_service_update(request, id, sector):
    config = _get_specialized_service_config(sector)
    item = get_object_or_404(SpecializedServiceContent, id=id, sector=sector)

    if request.method == "POST":
        item.title = request.POST.get("title")
        item.summary = request.POST.get("summary", "")
        item.content = request.POST.get("content")

        if "image" in request.FILES:
            item.image = request.FILES["image"]

        item.save()
        return redirect(config["list_url_name"])

    return render(
        request,
        "home/specialized_service_form.html",
        {"item": item, "service_config": config},
    )


@staff_required
def specialized_service_delete(request, id, sector):
    config = _get_specialized_service_config(sector)
    item = get_object_or_404(SpecializedServiceContent, id=id, sector=sector)
    item.delete()
    return redirect(config["list_url_name"])


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


# ====================== CRUD ABOUT STATEMENTS TYPE======================
@staff_required
def statement_type_list(request):
    statement_types = AboutStatementType.objects.all().order_by("order", "created_at")
    error = request.GET.get("error")
    return render(
        request,
        "home/about_statement_type_list.html",
        {"statement_types": statement_types, "error": error},
    )


@staff_required
def statement_type_create(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        order = request.POST.get("order") or 0
        is_active = request.POST.get("is_active") == "on"

        if not name:
            return render(
                request,
                "home/about_statement_type_form.html",
                {
                    "title": "Thêm loại nội dung",
                    "error": "Bạn cần nhập tên loại.",
                    "statement_type": {
                        "name": name,
                        "order": order,
                        "is_active": is_active,
                    },
                },
            )

        if AboutStatementType.objects.filter(name__iexact=name).exists():
            return render(
                request,
                "home/about_statement_type_form.html",
                {
                    "title": "Thêm loại nội dung",
                    "error": "Loại nội dung này đã tồn tại.",
                    "statement_type": {
                        "name": name,
                        "order": order,
                        "is_active": is_active,
                    },
                },
            )

        AboutStatementType.objects.create(
            name=name,
            order=int(order),
            is_active=is_active,
        )
        return redirect("statement_type_list")

    return render(
        request,
        "home/about_statement_type_form.html",
        {"title": "Thêm loại nội dung"},
    )


@staff_required
def statement_type_update(request, id):
    statement_type = get_object_or_404(AboutStatementType, id=id)

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        order = request.POST.get("order") or 0
        is_active = request.POST.get("is_active") == "on"

        if not name:
            return render(
                request,
                "home/about_statement_type_form.html",
                {
                    "title": "Sửa loại nội dung",
                    "error": "Bạn cần nhập tên loại.",
                    "statement_type": statement_type,
                },
            )

        duplicate = AboutStatementType.objects.filter(name__iexact=name).exclude(
            id=statement_type.id
        )
        if duplicate.exists():
            return render(
                request,
                "home/about_statement_type_form.html",
                {
                    "title": "Sửa loại nội dung",
                    "error": "Loại nội dung này đã tồn tại.",
                    "statement_type": statement_type,
                },
            )

        statement_type.name = name
        statement_type.slug = ""
        statement_type.order = int(order)
        statement_type.is_active = is_active
        statement_type.save()
        return redirect("statement_type_list")

    return render(
        request,
        "home/about_statement_type_form.html",
        {"title": "Sửa loại nội dung", "statement_type": statement_type},
    )


@staff_required
def statement_type_delete(request, id):
    statement_type = get_object_or_404(AboutStatementType, id=id)

    try:
        statement_type.delete()
    except ProtectedError:
        error = "Không thể xóa loại nội dung này vì vẫn còn nội dung đang sử dụng."
        return redirect(f"{reverse('statement_type_list')}?error={error}")

    return redirect("statement_type_list")


# ====================== CRUD ABOUT STATEMENTS ======================
@staff_required
def statement_list(request):
    statements = (
        AboutStatement.objects.select_related("statement_type")
        .all()
        .order_by(
            "statement_type__order",
            "statement_type__created_at",
            "order",
            "created_at",
        )
    )
    error = request.GET.get("error")
    return render(
        request,
        "home/about_statement_list.html",
        {"statements": statements, "error": error},
    )


@staff_required
def statement_create(request):
    statement_types = AboutStatementType.objects.filter(is_active=True).order_by(
        "order", "created_at"
    )

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        statement_type_id = (request.POST.get("statement_type") or "").strip()
        content = (request.POST.get("content") or "").strip()
        icon = (request.POST.get("icon") or "").strip()
        order = request.POST.get("order") or 0
        is_active = request.POST.get("is_active") == "on"

        if not statement_type_id or not content:
            return render(
                request,
                "home/about_statement_form.html",
                {
                    "title": "Thêm nội dung",
                    "types": statement_types,
                    "error": "Bạn cần chọn loại và nhập nội dung.",
                    "statement": {
                        "title": title,
                        "content": content,
                        "icon": icon,
                        "order": order,
                        "is_active": is_active,
                        "statement_type_id": statement_type_id,
                    },
                },
            )

        statement_type = get_object_or_404(AboutStatementType, id=statement_type_id)

        AboutStatement.objects.create(
            title=title,
            statement_type=statement_type,
            content=content,
            icon=icon,
            order=int(order),
            is_active=is_active,
        )
        return redirect("statement_list")

    return render(
        request,
        "home/about_statement_form.html",
        {
            "title": "Thêm nội dung",
            "types": statement_types,
        },
    )


@staff_required
def statement_update(request, id):
    statement = get_object_or_404(
        AboutStatement.objects.select_related("statement_type"), id=id
    )
    statement_types = AboutStatementType.objects.filter(is_active=True).order_by(
        "order", "created_at"
    )

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        statement_type_id = (request.POST.get("statement_type") or "").strip()
        content = (request.POST.get("content") or "").strip()
        icon = (request.POST.get("icon") or "").strip()
        order = request.POST.get("order") or 0
        is_active = request.POST.get("is_active") == "on"

        if not statement_type_id or not content:
            return render(
                request,
                "home/about_statement_form.html",
                {
                    "title": "Sửa nội dung",
                    "statement": statement,
                    "types": statement_types,
                    "error": "Bạn cần chọn loại và nhập nội dung.",
                },
            )

        statement_type = get_object_or_404(AboutStatementType, id=statement_type_id)

        statement.title = title
        statement.statement_type = statement_type
        statement.content = content
        statement.icon = icon
        statement.order = int(order)
        statement.is_active = is_active
        statement.save()
        return redirect("statement_list")

    return render(
        request,
        "home/about_statement_form.html",
        {
            "title": "Sửa nội dung",
            "statement": statement,
            "types": statement_types,
        },
    )


@staff_required
def statement_delete(request, id):
    statement = get_object_or_404(AboutStatement, id=id)
    statement.delete()
    return redirect("statement_list")


# ====================== CRUD SERVICE TYPES ======================
@staff_required
def service_type_list(request):
    service_types = ServiceType.objects.all().order_by("order", "created_at")
    error = request.GET.get("error")
    return render(
        request,
        "home/service_type_list.html",
        {"service_types": service_types, "error": error},
    )


@staff_required
def service_type_create(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        order = request.POST.get("order") or 0
        is_active = request.POST.get("is_active") == "on"

        if not name:
            return render(
                request,
                "home/service_type_form.html",
                {
                    "title": "Thêm loại dịch vụ",
                    "error": "Bạn cần nhập tên loại.",
                    "service_type": {
                        "name": name,
                        "order": order,
                        "is_active": is_active,
                    },
                },
            )

        if ServiceType.objects.filter(name__iexact=name).exists():
            return render(
                request,
                "home/service_type_form.html",
                {
                    "title": "Thêm loại dịch vụ",
                    "error": "Loại dịch vụ này đã tồn tại.",
                    "service_type": {
                        "name": name,
                        "order": order,
                        "is_active": is_active,
                    },
                },
            )

        ServiceType.objects.create(
            name=name,
            order=int(order),
            is_active=is_active,
        )
        return redirect("service_type_list")

    return render(
        request,
        "home/service_type_form.html",
        {"title": "Thêm loại dịch vụ"},
    )


@staff_required
def service_type_update(request, id):
    service_type = get_object_or_404(ServiceType, id=id)

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        order = request.POST.get("order") or 0
        is_active = request.POST.get("is_active") == "on"

        if not name:
            return render(
                request,
                "home/service_type_form.html",
                {
                    "title": "Sửa loại dịch vụ",
                    "error": "Bạn cần nhập tên loại.",
                    "service_type": service_type,
                },
            )

        duplicate = ServiceType.objects.filter(name__iexact=name).exclude(
            id=service_type.id
        )
        if duplicate.exists():
            return render(
                request,
                "home/service_type_form.html",
                {
                    "title": "Sửa loại dịch vụ",
                    "error": "Loại dịch vụ này đã tồn tại.",
                    "service_type": service_type,
                },
            )

        service_type.name = name
        service_type.slug = ""
        service_type.order = int(order)
        service_type.is_active = is_active
        service_type.save()
        return redirect("service_type_list")

    return render(
        request,
        "home/service_type_form.html",
        {"title": "Sửa loại dịch vụ", "service_type": service_type},
    )


@staff_required
def service_type_delete(request, id):
    service_type = get_object_or_404(ServiceType, id=id)

    try:
        service_type.delete()
    except ProtectedError:
        error = "Không thể xóa loại dịch vụ này vì vẫn còn dịch vụ đang sử dụng."
        return redirect(f"{reverse('service_type_list')}?error={error}")

    return redirect("service_type_list")


# ====================== CRUD SERVICES ======================
@staff_required
def service_list(request):
    query = (request.GET.get("q") or "").strip()
    services = (
        Service.objects.select_related("service_type")
        .all()
        .order_by(
            "service_type__order", "service_type__created_at", "order", "created_at"
        )
    )

    if query:
        services = services.filter(
            Q(title__icontains=query)
            | Q(content__icontains=query)
            | Q(icon__icontains=query)
            | Q(service_type__name__icontains=query)
        ).distinct()

    error = request.GET.get("error")
    return render(
        request,
        "home/service_list.html",
        {"services": services, "error": error, "query": query},
    )


@staff_required
def service_create(request):
    service_types = ServiceType.objects.filter(is_active=True).order_by(
        "order", "created_at"
    )

    if request.method == "POST":
        service_type_id = (request.POST.get("service_type") or "").strip()
        title = (request.POST.get("title") or "").strip()
        content = (request.POST.get("content") or "").strip()
        icon = (request.POST.get("icon") or "").strip()
        order = request.POST.get("order") or 0
        is_active = request.POST.get("is_active") == "on"

        if not service_type_id or not title or not content:
            return render(
                request,
                "home/service_form.html",
                {
                    "title_page": "Thêm dịch vụ",
                    "types": service_types,
                    "error": "Bạn cần chọn loại, nhập tiêu đề và nội dung.",
                    "service": {
                        "title": title,
                        "content": content,
                        "icon": icon,
                        "order": order,
                        "is_active": is_active,
                        "service_type_id": service_type_id,
                    },
                },
            )

        service_type = get_object_or_404(ServiceType, id=service_type_id)

        Service.objects.create(
            service_type=service_type,
            title=title,
            content=content,
            icon=icon,
            order=int(order),
            is_active=is_active,
        )
        return redirect("service_list")

    return render(
        request,
        "home/service_form.html",
        {
            "title_page": "Thêm dịch vụ",
            "types": service_types,
        },
    )


@staff_required
def service_update(request, id):
    service = get_object_or_404(Service.objects.select_related("service_type"), id=id)
    service_types = ServiceType.objects.filter(is_active=True).order_by(
        "order", "created_at"
    )

    if request.method == "POST":
        service_type_id = (request.POST.get("service_type") or "").strip()
        title = (request.POST.get("title") or "").strip()
        content = (request.POST.get("content") or "").strip()
        icon = (request.POST.get("icon") or "").strip()
        order = request.POST.get("order") or 0
        is_active = request.POST.get("is_active") == "on"

        if not service_type_id or not title or not content:
            return render(
                request,
                "home/service_form.html",
                {
                    "title_page": "Sửa dịch vụ",
                    "service": service,
                    "types": service_types,
                    "error": "Bạn cần chọn loại, nhập tiêu đề và nội dung.",
                },
            )

        service_type = get_object_or_404(ServiceType, id=service_type_id)

        service.service_type = service_type
        service.title = title
        service.content = content
        service.icon = icon
        service.order = int(order)
        service.is_active = is_active
        service.save()
        return redirect("service_list")

    return render(
        request,
        "home/service_form.html",
        {
            "title_page": "Sửa dịch vụ",
            "service": service,
            "types": service_types,
        },
    )


@staff_required
def service_delete(request, id):
    service = get_object_or_404(Service, id=id)
    service.delete()
    return redirect("service_list")


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

    return render(
        request,
        "home/about_certificate_form.html",
        {
            "title": "Thêm chứng chỉ mới",
            "icon_choices": Certificate.ICON_CHOICES,
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
        elif not _can_move_consultation_status(consultation.status, new_status):
            messages.error(
                request,
                "Không thể cập nhật trạng thái lùi về bước trước.",
            )
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
            "allowed_statuses": {
                value
                for value, _ in Consultation.STATUS_CHOICES
                if _can_move_consultation_status(consultation.status, value)
            },
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


@staff_required
def about_video_tour_edit(request):
    video_tour = AboutVideoTour.objects.first()

    if request.method == "POST":
        data = request.POST
        if video_tour is None:
            video_tour = AboutVideoTour()

        video_tour.section_title = data.get("section_title", "").strip()
        video_tour.section_description = data.get("section_description", "").strip()
        video_tour.step_1_icon = data.get("step_1_icon", "").strip()
        video_tour.step_1_title = data.get("step_1_title", "").strip()
        video_tour.step_1_description = data.get("step_1_description", "").strip()
        video_tour.step_2_icon = data.get("step_2_icon", "").strip()
        video_tour.step_2_title = data.get("step_2_title", "").strip()
        video_tour.step_2_description = data.get("step_2_description", "").strip()
        video_tour.step_3_icon = data.get("step_3_icon", "").strip()
        video_tour.step_3_title = data.get("step_3_title", "").strip()
        video_tour.step_3_description = data.get("step_3_description", "").strip()
        video_tour.save()
        messages.success(request, "Đã cập nhật phần video tour / quy trình!")
        return redirect("about_video_tour_edit")

    return render(
        request, "home/about_video_tour_form.html", {"video_tour": video_tour}
    )


# ===============why_choose_section_edit
@staff_required
def why_choose_section_edit(request):
    section = HomeWhyChooseSection.objects.first()
    if not section:
        section = HomeWhyChooseSection.objects.create()

    if request.method == "POST":
        section.section_title = (request.POST.get("section_title") or "").strip()
        section.right_kicker = (request.POST.get("right_kicker") or "").strip()
        section.right_title = (request.POST.get("right_title") or "").strip()
        section.right_subtitle = (request.POST.get("right_subtitle") or "").strip()
        section.badge_number = (request.POST.get("badge_number") or "").strip()
        section.badge_label = (request.POST.get("badge_label") or "").strip()
        section.save()
        return redirect("why_choose_item_list")

    return render(
        request,
        "home/why_choose_section_form.html",
        {"section": section, "title": "Chỉnh sửa khối Tại Sao Chọn Chúng Tôi"},
    )


@staff_required
def why_choose_item_list(request):
    items = (
        HomeWhyChooseItem.objects.select_related("section")
        .all()
        .order_by("order", "created_at")
    )
    return render(request, "home/why_choose_item_list.html", {"items": items})


@staff_required
def why_choose_item_create(request):
    section = HomeWhyChooseSection.objects.first()
    if not section:
        section = HomeWhyChooseSection.objects.create()

    if request.method == "POST":
        title = (request.POST.get("title") or "").strip()
        content = (request.POST.get("content") or "").strip()
        icon = (request.POST.get("icon") or "").strip()
        order = request.POST.get("order") or 0
        is_active = request.POST.get("is_active") == "on"

        if title and content:
            HomeWhyChooseItem.objects.create(
                section=section,
                title=title,
                content=content,
                icon=icon or "fa-solid fa-star",
                order=int(order),
                is_active=is_active,
            )
            return redirect("why_choose_item_list")

    return render(
        request,
        "home/why_choose_item_form.html",
        {"title_page": "Thêm lý do", "item": None},
    )


@staff_required
def why_choose_item_update(request, id):
    item = get_object_or_404(HomeWhyChooseItem, id=id)

    if request.method == "POST":
        item.title = (request.POST.get("title") or "").strip()
        item.content = (request.POST.get("content") or "").strip()
        item.icon = (request.POST.get("icon") or "").strip() or "fa-solid fa-star"
        item.order = int(request.POST.get("order") or 0)
        item.is_active = request.POST.get("is_active") == "on"
        item.save()
        return redirect("why_choose_item_list")

    return render(
        request,
        "home/why_choose_item_form.html",
        {"title_page": "Sửa lý do", "item": item},
    )


@staff_required
def why_choose_item_delete(request, id):
    item = get_object_or_404(HomeWhyChooseItem, id=id)
    item.delete()
    return redirect("why_choose_item_list")

# ====================== CRUD HERO ======================
@staff_required
def hero_edit(request):
    hero = HeroSection.objects.first()

    if request.method == "POST":
        if hero is None:
            hero = HeroSection()

        # Text
        hero.badge_text = request.POST.get("badge_text", "").strip()
        hero.heading_line1 = request.POST.get("heading_line1", "").strip()
        hero.heading_line2 = request.POST.get("heading_line2", "").strip()
        hero.description = request.POST.get("description", "").strip()
        hero.btn_primary_text = request.POST.get("btn_primary_text", "").strip()
        hero.btn_primary_url = request.POST.get("btn_primary_url", "").strip()
        hero.btn_outline_text = request.POST.get("btn_outline_text", "").strip()
        hero.btn_outline_url = request.POST.get("btn_outline_url", "").strip()
        hero.text_theme = request.POST.get("text_theme", "light").strip() or "light"

        # Stats
        hero.stat_1_num = request.POST.get("stat_1_num", "").strip()
        hero.stat_1_label = request.POST.get("stat_1_label", "").strip()
        hero.stat_2_num = request.POST.get("stat_2_num", "").strip()
        hero.stat_2_label = request.POST.get("stat_2_label", "").strip()
        hero.stat_3_num = request.POST.get("stat_3_num", "").strip()
        hero.stat_3_label = request.POST.get("stat_3_label", "").strip()
        hero.stat_4_num = request.POST.get("stat_4_num", "").strip()
        hero.stat_4_label = request.POST.get("stat_4_label", "").strip()

        # Background
        hero.bg_type = request.POST.get("bg_type", "color")
        if "bg_image" in request.FILES:
            hero.bg_image = request.FILES["bg_image"]
        if "bg_video" in request.FILES:
            hero.bg_video = request.FILES["bg_video"]

        hero.save()

        # Carousel images — xử lý nhiều file
        carousel_files = request.FILES.getlist("carousel_images")
        for f in carousel_files:
            last_order = HeroCarouselImage.objects.filter(hero=hero).count()
            HeroCarouselImage.objects.create(hero=hero, image=f, order=last_order)

        messages.success(request, "Đã cập nhật Hero section!")
        return redirect("hero_edit")

    carousel_images = HeroCarouselImage.objects.filter(hero=hero) if hero else []
    return render(request, "home/hero_form.html", {
        "hero": hero,
        "carousel_images": carousel_images,
        "bg_type_choices": HeroSection.BG_TYPE_CHOICES,
        "text_theme_choices": HeroSection.TEXT_THEME_CHOICES,
    })


@staff_required
def hero_carousel_delete(request, id):
    img = get_object_or_404(HeroCarouselImage, id=id)
    img.delete()
    return redirect("hero_edit")


@staff_required
def partner_list(request):
    partners = Partner.objects.all().order_by("order", "created_at")
    return render(request, "home/partner_list.html", {"partners": partners})


@staff_required
def partner_create(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        website_url = (request.POST.get("website_url") or "").strip()
        order = int(request.POST.get("order") or 0)
        is_active = request.POST.get("is_active") == "on"

        if not name:
            return render(
                request,
                "home/partner_form.html",
                {
                    "title_page": "Thêm đối tác",
                    "error": "Bạn cần nhập tên đối tác.",
                },
            )

        Partner.objects.create(
            name=name,
            website_url=website_url,
            order=order,
            is_active=is_active,
            logo=request.FILES.get("logo"),
        )
        messages.success(request, "Đã thêm đối tác.")
        return redirect("partner_list")

    return render(
        request,
        "home/partner_form.html",
        {"title_page": "Thêm đối tác"},
    )


@staff_required
def partner_update(request, id):
    partner = get_object_or_404(Partner, id=id)

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        website_url = (request.POST.get("website_url") or "").strip()

        if not name:
            return render(
                request,
                "home/partner_form.html",
                {
                    "title_page": "Sửa đối tác",
                    "partner": partner,
                    "error": "Bạn cần nhập tên đối tác.",
                },
            )

        partner.name = name
        partner.website_url = website_url
        partner.order = int(request.POST.get("order") or 0)
        partner.is_active = request.POST.get("is_active") == "on"

        if "logo" in request.FILES:
            partner.logo = request.FILES["logo"]

        partner.save()
        messages.success(request, "Đã cập nhật đối tác.")
        return redirect("partner_list")

    return render(
        request,
        "home/partner_form.html",
        {"title_page": "Sửa đối tác", "partner": partner},
    )


@staff_required
def partner_delete(request, id):
    partner = get_object_or_404(Partner, id=id)
    partner.delete()
    messages.success(request, "Đã xóa đối tác.")
    return redirect("partner_list")
