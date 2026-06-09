import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from channels.sessions import CookieMiddleware
from django.core.asgi import get_asgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

django_asgi_application = get_asgi_application()

from backend.apps.matches.routing import websocket_urlpatterns


application = ProtocolTypeRouter(
    {
        "http": django_asgi_application,
        "websocket": AllowedHostsOriginValidator(
            CookieMiddleware(URLRouter(websocket_urlpatterns))
        ),
    }
)
