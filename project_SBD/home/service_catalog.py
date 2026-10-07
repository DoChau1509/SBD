"""Shared helpers for links in the public service catalogue."""

from django.urls import NoReverseMatch, reverse


SERVICE_TYPE_PUBLIC_URL_NAMES = {
    "dan-dung": "civil",
    "cong-nghiep": "industrial",
    "thiet-ke-khong-gian-giao-duc": "education_space_design",
    "nang-luong-cong-trinh-xanh": "energy_green",
    "noi-that-thuong-mai": "interior_commercial",
}


def service_type_public_url(service_type):
    """Return the canonical public page for a service type."""
    url_name = SERVICE_TYPE_PUBLIC_URL_NAMES.get(service_type.slug)
    try:
        if url_name:
            return reverse(url_name)
        return reverse("service_type_public", kwargs={"slug": service_type.slug})
    except NoReverseMatch:
        return reverse("home")
