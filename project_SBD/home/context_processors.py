from .models import ContactInfo, Notification


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

    return {
        "site_contact": contact,
        "unread_notifications_count": unread_notifications_count,
        "recent_notifications": recent_notifications,
    }
