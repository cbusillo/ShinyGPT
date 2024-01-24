import logging
import os
from importlib import import_module

from channels.auth import AuthMiddlewareStack  # type: ignore
from channels.routing import ProtocolTypeRouter, URLRouter  # type: ignore
from django.core.asgi import get_asgi_application

logging.basicConfig(level=logging.DEBUG)


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "manage_django.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(
                # Import routing module here
                import_module("manage_django.routing").websocket_urlpatterns
            )
        ),
    }
)
