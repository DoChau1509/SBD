from .models import (
    ContactInfo,
    Notification,
    Consultation,
    StaffLoginActivityAccess,
    SiteBrandSettings,
)
from django.db import DatabaseError


MANAGEMENT_URL_GROUPS = {
    "projects": {
        "dashboard",
        "project_add",
        "project_edit",
        "project_delete",
        "featured_project_list",
        "project_category_list",
        "project_category_add",
        "project_category_edit",
        "project_category_delete",
    },
    "products_posts": {
        "product_list",
        "product_add",
        "product_edit",
        "product_delete",
        "product_category_list",
        "product_category_add",
        "product_category_edit",
        "product_category_delete",
        "post_list",
        "post_add",
        "post_edit",
        "post_delete",
        "post_category_list",
        "post_category_add",
        "post_category_edit",
        "post_category_delete",
    },
    "services": {
        "service_list",
        "service_add",
        "service_edit",
        "service_delete",
        "service_type_list",
        "service_type_add",
        "service_type_edit",
        "service_type_delete",
        "office_rental_list",
        "office_rental_add",
        "office_rental_edit",
        "office_rental_delete",
        "education_space_design_list",
        "education_space_design_add",
        "education_space_design_edit",
        "education_space_design_delete",
        "industrial_list",
        "industrial_add",
        "industrial_edit",
        "industrial_delete",
        "civil_list",
        "civil_add",
        "civil_edit",
        "civil_delete",
        "energy_green_list",
        "energy_green_add",
        "energy_green_edit",
        "energy_green_delete",
        "interior_commercial_list",
        "interior_commercial_add",
        "interior_commercial_edit",
        "interior_commercial_delete",
    },
    "site_content": {
        "hero_edit",
        "why_choose_section_edit",
        "why_choose_item_list",
        "why_choose_item_add",
        "why_choose_item_edit",
        "why_choose_item_delete",
        "partner_list",
        "partner_add",
        "partner_edit",
        "partner_delete",
        "about_intro_edit",
        "statement_list",
        "statement_add",
        "statement_edit",
        "statement_delete",
        "statement_type_list",
        "statement_type_add",
        "statement_type_edit",
        "statement_type_delete",
        "about_video_tour_edit",
        "leadership_list",
        "leadership_add",
        "leadership_edit",
        "leadership_delete",
        "certificate_list",
        "certificate_add",
        "certificate_edit",
        "certificate_delete",
    },
    "contact": {
        "contact_info_list",
        "contact_info_add",
        "contact_info_edit",
        "contact_info_delete",
        "contact_info_toggle_status",
        "faq_list",
        "faq_add",
        "faq_edit",
        "faq_delete",
        "consultation_list",
        "consultation_detail",
    },
    "system": {
        "system_settings",
        "site_logo",
        "email_otp_settings",
        "staff_account_list",
        "staff_account_add",
        "staff_account_edit",
        "staff_account_toggle_status",
        "staff_login_activity",
        "staff_map",
        "staff_map_snapshot",
        "staff_map_position_add",
        "staff_map_position_update",
        "staff_map_position_delete",
    },
}

MANAGEMENT_URL_NAMES = set().union(*MANAGEMENT_URL_GROUPS.values())


def site_contact(request):
    contact = (
        ContactInfo.objects.filter(is_active=True)
        .order_by("order", "created_at")
        .first()
    )
    unread_notifications_count = 0
    recent_notifications = []

    if request.user.is_authenticated:
        unread_notifications_count = Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).count()
        recent_notifications = Notification.objects.filter(user=request.user)[:5]
        
    consultations_unfinished = Consultation.objects.exclude(status="done").count()
    brand_settings = SiteBrandSettings.get_solo()
    current_url_name = (
        request.resolver_match.url_name if request.resolver_match else ""
    )
    management_group = next(
        (
            group_name
            for group_name, url_names in MANAGEMENT_URL_GROUPS.items()
            if current_url_name in url_names
        ),
        "",
    )
    can_view_staff_login_activity = False
    if request.user.is_authenticated:
        if request.user.is_superuser:
            can_view_staff_login_activity = True
        else:
            try:
                can_view_staff_login_activity = StaffLoginActivityAccess.objects.filter(
                    user=request.user,
                ).exists()
            except DatabaseError:
                can_view_staff_login_activity = False

    return {
        "site_contact": contact,
        "brand_settings": brand_settings,
        "unread_notifications_count": unread_notifications_count,
        "recent_notifications": recent_notifications,
        "consultations_unfinished": consultations_unfinished,
        "show_management_nav": (
            request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
            and current_url_name in MANAGEMENT_URL_NAMES
        ),
        "can_view_staff_login_activity": can_view_staff_login_activity,
        "management_url_name": current_url_name,
        "management_group": management_group,
    }
