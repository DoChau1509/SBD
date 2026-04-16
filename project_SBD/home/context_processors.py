from .models import ContactInfo


def site_contact(request):
    return {
        "site_contact": ContactInfo.objects.filter(is_active=True)
        .order_by("order", "created_at")
        .first()
    }
