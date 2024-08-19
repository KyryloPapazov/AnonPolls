from django.test import TestCase
from django.urls import reverse
from http import HTTPStatus

from users.models import User
from polls.models import Survey
# Create your tests here.

class IndexViewTestCase(TestCase):

    def test_view(self):
        path = reverse('index') # 'http://127.0.0.1:8000/'
        response = self.client.get(path)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context_data['title'],'Polls')
        self.assertTemplateUsed(response, 'polls/index.html')




class PollsListViewTestCase(TestCase):

    def test_list(self):
        path = reverse('polls:index')
        response = self.client.get(path)

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context_data['title'], 'Polls')
        self.assertTemplateUsed(response, 'polls/polls.html')


