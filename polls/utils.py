from functools import wraps
from typing import Callable, Any
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse

from AnonPolls import settings
from .models import Survey

import requests
import hashlib

import uuid


def generate_unique_identifier():
    return str(uuid.uuid4())


def user_is_author(view_func: Callable[..., HttpResponse]) -> Callable[..., HttpResponse]:
    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        if not isinstance(request, HttpRequest):
            raise AttributeError("Request object is not an instance of HttpRequest.")

        survey = get_object_or_404(Survey, slug=kwargs['survey_slug'])
        if survey.author != request.user:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({"error": "Тільки творець опитувань має доступ до цієї сторінки."}, status=403)
            else:
                messages.error(request, "Тільки творець опитувань має доступ до цієї сторінки.")
                return redirect(reverse('index'))
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def verify_recaptcha(token, threshold=0.9):
    url = 'https://www.google.com/recaptcha/api/siteverify'
    data = {
        'secret': settings.RECAPTCHA_PRIVATE_KEY,
        'response': token
    }
    response = requests.post(url, data=data)
    result = response.json()
    return result.get('success') and result.get('score', 0) >= threshold


def validate_questions_data(questions):
    for q in questions:
        if 'text' not in q or not q['text']:
            return False, "All questions must have text."
        if 'question_type' not in q or not q['question_type']:
            return False, "All questions must have a type."
        if q['question_type'] == 'scale':
            options = q.get('options')
            if not options or len(options) != 2:
                return False, "Scale questions must have min and max values."
            try:
                min_value, max_value = int(options[0]), int(options[1])
            except ValueError:
                return False, "Scale min and max values must be numeric."
            if min_value < -10000 or max_value > 10000:
                return False, "Scale min and max values must be between -10000 and 10000."
    return True, ""
