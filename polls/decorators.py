# decorators.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from functools import wraps


def email_verified_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        if not request.user.is_verified:  # Assuming 'email_verified' is a field in your User model
            return redirect('users:EmailVerificationUnCompleteView')
        return view_func(request, *args, **kwargs)

    return login_required(_wrapped_view)
