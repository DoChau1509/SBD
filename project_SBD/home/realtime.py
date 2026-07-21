from asgiref.sync import async_to_sync


STAFF_MAP_GROUP = "staff_map"


def broadcast_staff_map_update():
    try:
        from channels.layers import get_channel_layer
    except ImportError:
        return

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        STAFF_MAP_GROUP,
        {
            "type": "staff_map.changed",
        },
    )
