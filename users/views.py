from django.contrib.auth.views import LoginView, LogoutView
from users.forms import UserLoginForm
from django.urls import reverse_lazy
from common.views import TitleMixin


# Create your views here.

class UserLoginView(TitleMixin, LoginView):
    title = 'Авторизація'
    template_name = 'users/login.html'
    form_class = UserLoginForm


class UserLogoutView(TitleMixin, LogoutView):
    title = 'Вихід'
    next_page = reverse_lazy('index')

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        return response

# class UserRegisterView(TitleMixin, SuccessMessageMixin, CreateView):
#     title = 'Реєстрація'
#     model = User
#     form_class = UserRegisterForm
#     template_name = 'users/registration.html'
#     success_url = reverse_lazy('users:login')
#     success_message = 'Обліковий запис було успішно створено!'

#
# class UserProfileView(TitleMixin, UpdateView):
#     model = User
#     form_class = UserProfileForm
#     template_name = 'users/profile.html'
#     title = 'Особистий кабінет'
#
#     def get_object(self):
#         return get_object_or_404(User, pk=self.request.user.pk)
#
#     def get_success_url(self):
#         return reverse('users:profile', args=[self.object.id])
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         user = self.request.user
#         context['authors'] = Survey.objects.filter(author=user)
#         return context
#
#
# class EmailVerificationView(TitleMixin, TemplateView):
#     title = 'Підтверддження пошти'
#     template_name = 'users/email_verification.html'
#
#     def get(self, request, *args, **kwargs):
#         code = kwargs['code']
#         user = User.objects.get(email=kwargs['email'])
#         email_verification = EmailVerification.objects.filter(user=user, code=code)
#         if email_verification.exists() and not email_verification.first().is_expired():
#             user.is_verified_email = True
#             user.save()
#             return super(EmailVerificationView, self).get(request, *args, **kwargs)
#         else:
#             return HttpResponseRedirect(reverse('index'))
#
#
# class ForgotPasswordView(TemplateView):
#     title = 'Підтверддження пошти'
#     template_name = 'users/forgot_password.html'
#
#     def get(self, request, *args, **kwargs):
#         form = PasswordResetForm()
#         return self.render_to_response({'form': form})
#
#     def post(self, request, *args, **kwargs):
#         form = PasswordResetForm(request.POST)
#         if form.is_valid():
#             email = form.cleaned_data['email']
#             users = User.objects.filter(email=email)
#             if users.exists():
#                 for user in users:
#                     token = default_token_generator.make_token(user)
#                     uid = urlsafe_base64_encode(force_bytes(user.pk))
#                     url = request.build_absolute_uri(f"/users/reset-password/{uid}/{token}/")
#                     message = render_to_string('users/password_reset_email.html', {
#                         'user': user,
#                         'url': url,
#                     })
#                     send_mail(
#                         'Password Reset Request',
#                         message,
#                         settings.EMAIL_HOST_USER,
#                         [user.email],
#                         fail_silently=False,
#                     )
#                 return redirect('users:reset-password')
#         return self.render_to_response({'form': form})
#
#
# class ResetPasswordView(TemplateView):
#     title = 'Відновлення пароля'
#     template_name = 'users/reset_password.html'
#
#     def get(self, request, uidb64, token, *args, **kwargs):
#         try:
#             uid = force_str(urlsafe_base64_decode(uidb64))
#             user = User.objects.get(pk=uid)
#         except (TypeError, ValueError, OverflowError, User.DoesNotExist):
#             user = None
#
#         if user is not None and default_token_generator.check_token(user, token):
#             form = SetPasswordForm(user)
#             return self.render_to_response({'form': form})
#         else:
#             return self.render_to_response({'error': 'Invalid link'})
#
#     def post(self, request, uidb64, token, *args, **kwargs):
#         try:
#             uid = force_str(urlsafe_base64_decode(uidb64))
#             user = User.objects.get(pk=uid)
#         except (TypeError, ValueError, OverflowError, User.DoesNotExist):
#             user = None
#
#         if user is not None and default_token_generator.check_token(user, token):
#             form = SetPasswordForm(user, request.POST)
#             if form.is_valid():
#                 form.save()
#                 return redirect('users:login')
#             return self.render_to_response({'form': form})
#         else:
#             return self.render_to_response({'error': 'Invalid link'})
