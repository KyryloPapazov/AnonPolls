import uuid

from unidecode import unidecode
from django.db import models
from django.utils.text import slugify

from AnonPolls import settings


class Survey(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True, max_length=255)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    show_author = models.BooleanField(default=False)
    survey_visibility = models.CharField(max_length=10, choices=[('public', 'Public'), ('private', 'Private')])
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            # Перетворюємо заголовок в ASCII, використовуючи unidecode
            title_transliterated = unidecode(self.title)
            # Створюємо slug
            self.slug = slugify(title_transliterated + "-" + str(uuid.uuid4())[:8])
        super(Survey, self).save(*args, **kwargs)

    def __str__(self):
        return self.title


class Question(models.Model):
    TEXT = 'text'
    MULTIPLE_CHOICE = 'multiple_choice'
    SCALE = 'scale'

    QUESTION_TYPES = [
        (TEXT, 'Text'),
        (MULTIPLE_CHOICE, 'Multiple Choice'),
        (SCALE, 'Scale'),
    ]

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES)
    min_value = models.IntegerField(null=True, blank=True)
    max_value = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.text


class AnswerOption(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    option_text = models.CharField(max_length=255)

    def __str__(self):
        return self.option_text


class Response(models.Model):
    survey_question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.TextField()
    respondent_identifier = models.CharField(max_length=36)
    structured_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('survey_question', 'respondent_identifier')

    def __str__(self):
        return self.answer


class QuestionLogic(models.Model):
    question = models.ForeignKey(Question, related_name='current_question', on_delete=models.CASCADE)
    target_question = models.ForeignKey(Question, related_name='next_question', on_delete=models.CASCADE)
    trigger_answer = models.TextField()

    def __str__(self):
        return f"If {self.question.text} is '{self.trigger_answer}', go to {self.target_question.text}"
