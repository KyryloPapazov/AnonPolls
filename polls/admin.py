# surveys/admin.py

from django.contrib import admin
from .models import Survey, Question, AnswerOption, Response, QuestionLogic

admin.site.register(Survey)
admin.site.register(Question)
admin.site.register(AnswerOption)
admin.site.register(Response)
admin.site.register(QuestionLogic)

