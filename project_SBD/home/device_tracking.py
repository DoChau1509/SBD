import uuid

from django.db import DatabaseError
from django.utils import timezone

from .models import StaffDevice

STAFF_DEVICE_COOKIE_NAME = "sbd_staff_device_id"
STAFF_DEVICE_SESSION_KEY = "staff_device_id"
STAFF_DEVICE_COOKIE_MAX_AGE = 60 * 60 * 24 * 365


def is_staff_or_admin(user):
    return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))


def get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR") or None


def parse_device_info(user_agent):
    user_agent = user_agent or ""
    lower_agent = user_agent.lower()

    if "edg/" in lower_agent:
        browser = "Microsoft Edge"
    elif "chrome/" in lower_agent and "chromium" not in lower_agent:
        browser = "Chrome"
    elif "firefox/" in lower_agent:
        browser = "Firefox"
    elif "safari/" in lower_agent and "chrome/" not in lower_agent:
        browser = "Safari"
    else:
        browser = "Trình duyệt không xác định"

    if "windows" in lower_agent:
        platform = "Windows"
    elif "android" in lower_agent:
        platform = "Android"
    elif "iphone" in lower_agent or "ipad" in lower_agent:
        platform = "iOS"
    elif "mac os" in lower_agent or "macintosh" in lower_agent:
        platform = "macOS"
    elif "linux" in lower_agent:
        platform = "Linux"
    else:
        platform = "thiết bị không xác định"

    if "ipad" in lower_agent or "tablet" in lower_agent:
        device_type = "máy tính bảng"
    elif "mobile" in lower_agent or "iphone" in lower_agent or "android" in lower_agent:
        device_type = "điện thoại"
    else:
        device_type = "máy tính"

    label = f"{browser} trên {platform} ({device_type})"
    return {
        "browser_label": browser,
        "platform_label": platform,
        "device_type": device_type,
        "device_label": label,
    }


def get_or_create_staff_device(request, user):
    if not is_staff_or_admin(user):
        return None, ""

    device_id = (
        request.COOKIES.get(STAFF_DEVICE_COOKIE_NAME)
        or request.session.get(STAFF_DEVICE_SESSION_KEY)
        or uuid.uuid4().hex
    )
    request.session[STAFF_DEVICE_SESSION_KEY] = device_id

    user_agent = request.META.get("HTTP_USER_AGENT", "")
    device_info = parse_device_info(user_agent)

    try:
        device, _ = StaffDevice.objects.get_or_create(
            user=user,
            device_id=device_id,
            defaults={
                "user_agent": user_agent,
                **{
                    key: value
                    for key, value in device_info.items()
                    if key != "device_label"
                },
            },
        )
        StaffDevice.objects.filter(pk=device.pk).update(
            user_agent=user_agent,
            browser_label=device_info["browser_label"],
            platform_label=device_info["platform_label"],
            device_type=device_info["device_type"],
            last_seen_at=timezone.now(),
        )
        device.refresh_from_db()
        return device, device_info["device_label"]
    except DatabaseError:
        return None, device_info["device_label"]
