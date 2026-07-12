from .device_tracking import (
    STAFF_DEVICE_COOKIE_MAX_AGE,
    STAFF_DEVICE_COOKIE_NAME,
    STAFF_DEVICE_SESSION_KEY,
    is_staff_or_admin,
)


class StaffDeviceCookieMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if is_staff_or_admin(getattr(request, "user", None)):
            device_id = request.session.get(STAFF_DEVICE_SESSION_KEY)
            if device_id:
                response.set_cookie(
                    STAFF_DEVICE_COOKIE_NAME,
                    device_id,
                    max_age=STAFF_DEVICE_COOKIE_MAX_AGE,
                    httponly=True,
                    samesite="Lax",
                    secure=request.is_secure(),
                )

        return response
