from django.http import JsonResponse, HttpRequest
from components.lang_model_service import LLMClient


def get_gpt_models(request: HttpRequest) -> JsonResponse:
    gpt_model_names = list(LLMClient.get_model_names())
    return JsonResponse({"gpt_models": gpt_model_names})
