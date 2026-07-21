from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db import DatabaseError
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils import timezone

from .device_tracking import get_client_ip, get_or_create_staff_device, is_staff_or_admin
from .models import StaffLoginActivity, StaffMap, StaffMapPosition
from .realtime import broadcast_staff_map_update


@receiver(user_logged_in)
def record_staff_login(sender, request, user, **kwargs):
    if not is_staff_or_admin(user):
        return

    try:
        if not request.session.session_key:
            request.session.save()

        user_agent = request.META.get("HTTP_USER_AGENT", "")
        device, device_label = get_or_create_staff_device(request, user)
        StaffLoginActivity.objects.create(
            user=user,
            device=device,
            session_key=request.session.session_key or "",
            status=StaffLoginActivity.STATUS_ACTIVE,
            ip_address=get_client_ip(request),
            user_agent=user_agent,
            device_identifier=device.device_id if device else request.session.get("staff_device_id", ""),
            device_name=device.display_name if device else "",
            device_label=device_label,
        )
        broadcast_staff_map_update()
    except DatabaseError:
        pass


@receiver(user_logged_out)
def record_staff_logout(sender, request, user, **kwargs):
    if not is_staff_or_admin(user):
        return

    try:
        active_sessions = StaffLoginActivity.objects.filter(
            user=user,
            status=StaffLoginActivity.STATUS_ACTIVE,
        )
        session_key = request.session.session_key
        if session_key:
            active_sessions = active_sessions.filter(session_key=session_key)

        updated = active_sessions.update(
            status=StaffLoginActivity.STATUS_LOGGED_OUT,
            logout_at=timezone.now(),
        )
        if updated:
            broadcast_staff_map_update()
            return

        latest_activity = (
            StaffLoginActivity.objects.filter(
                user=user,
                status=StaffLoginActivity.STATUS_ACTIVE,
            )
            .order_by("-login_at", "-id")
            .first()
        )
        if latest_activity:
            latest_activity.status = StaffLoginActivity.STATUS_LOGGED_OUT
            latest_activity.logout_at = timezone.now()
            latest_activity.save(update_fields=["status", "logout_at"])
            broadcast_staff_map_update()
    except DatabaseError:
        pass


@receiver(post_save, sender=StaffMap)
@receiver(post_delete, sender=StaffMap)
@receiver(post_save, sender=StaffMapPosition)
@receiver(post_delete, sender=StaffMapPosition)
def broadcast_staff_map_model_change(sender, instance, **kwargs):
    broadcast_staff_map_update()
