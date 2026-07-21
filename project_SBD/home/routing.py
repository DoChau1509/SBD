from django.urls import path

from . import consumers


websocket_urlpatterns = [
    path("ws/staff-map/", consumers.StaffMapConsumer.as_asgi()),
]
