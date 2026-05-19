from .models import ContactInfo, Notification, Consultation, SiteBrandSettings


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

    return {
        "site_contact": contact,
        "brand_settings": brand_settings,
        "unread_notifications_count": unread_notifications_count,
        "recent_notifications": recent_notifications,
        "consultations_unfinished": consultations_unfinished,
    }
