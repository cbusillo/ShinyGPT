from django.urls import path
from . import views

urlpatterns = [
    path("gpt_models", views.get_gpt_models),
]
