from django import forms
from django.contrib.auth.forms import AuthenticationForm
from users.models import User


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control py-4',
                                                             'placeholder': "Введіть ім`я користувача"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control py-4',
                                                                 'placeholder': 'Введіть пароль'}))

    class Meta:
        model = User
        fields = ('username', 'password')


# class UserRegisterForm(UserCreationForm):
#     first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control py-4',
#                                                                'placeholder': 'Введіть ім`я'}))
#     last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control py-4',
#                                                               'placeholder': 'Введіть прізвище'}))
#     username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control py-4',
#                                       'placeholder': 'Введіть ім`я користувача'}))
#     email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control py-4',
#                                                             'placeholder': 'Введіть адресу ел. пошти'}))
#     password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control py-4',
#                                                                   'placeholder': 'Введіть пароль'}))
#     password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control py-4',
#                                                                   'placeholder': 'Введіть пароль повторно'}))
#
#     class Meta:
#         model = User
#         fields = ('first_name', 'last_name', 'username', 'email', 'password1', 'password2')
#
#     def clean_email(self):
#         email = self.cleaned_data.get('email')
#         if User.objects.filter(email=email).exists():
#             raise ValidationError('Обліковий запис з такою поштою вже існує.')
#         return email
#
#     def save(self, commit=True):
#         user = super(UserRegisterForm, self).save(commit=True)
#         send_email_verify.delay(user.id)
#         return user
#
#
# class UserProfileForm(UserChangeForm):
#     first_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control py-4'}))
#     last_name = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control py-4'}))
#     image = forms.ImageField(widget=forms.FileInput(attrs={'class': 'custom-file-input'}), required=False)
#     username = forms.CharField(
#         widget=forms.TextInput(attrs={'class': 'form-control py-4', 'readonly': True}))
#     email = forms.EmailField(
#         widget=forms.EmailInput(attrs={'class': 'form-control py-4', 'readonly': True}))
#
#     class Meta:
#         model = User
#         fields = ('first_name', 'last_name', 'image', 'username', 'email')
#
#
#
