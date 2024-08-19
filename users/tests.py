from django.test import TestCase
from django.urls import reverse
from http import HTTPStatus

from users.models import User
from users.forms import UserRegisterForm, EmailVerification


# Create your tests here.


class UserRegisterViewTests(TestCase):

    def setUp(self):
        self.path = reverse('users:register')

    def test_user_register_get(self):
        response = self.client.get(self.path)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context_data['title'], 'Register')
        self.assertTemplateUsed(response, 'users/register.html')

    def test_user_register_post_success(self):
        data = {
            'first_name': 'John', 'last_name': 'Doe',
            'username': 'johndoe', 'email': 'papazovk12@gmail.com',
            'password1': 'Papzar2002', 'password2': 'Papzar2002',
        }
        response = self.client.post(self.path, data)

        username = data['username']

        # check creat user
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        # self.assertRedirects(response, reverse('users:login'))
        self.assertTrue(User.objects.filter(username=username).exists())

        # check creat email verify
        


