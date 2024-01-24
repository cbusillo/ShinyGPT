# routing.py
from django.urls import re_path

from api_django import consumers

websocket_urlpatterns = [
    re_path(r"generate", consumers.GenerateConsumer.as_asgi()),
]
