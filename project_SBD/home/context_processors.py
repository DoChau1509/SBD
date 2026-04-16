from .models import ContactInfo


def site_contact(request):
    contact = (
        ContactInfo.objects.filter(is_active=True)
        .order_by("order", "created_at")
        .first()
    )
    return {"site_contact": contact}
