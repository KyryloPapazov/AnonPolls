# surveys/forms.py

from django import forms
from django.forms import inlineformset_factory
from .models import Survey, Question, AnswerOption

# from snowpenguin.django.recaptcha3.fields import ReCaptchaField
#
#
# class SurveyForm(forms.Form):
#     captcha = ReCaptchaField()


class SurveyResponseForm(forms.Form):
    def __init__(self, *args, **kwargs):
        questions = kwargs.pop('questions')
        super().__init__(*args, **kwargs)
        for question in questions:
            field_name = f'question_{question.id}'
            if question.question_type == Question.TEXT:
                self.fields[field_name] = forms.CharField(label=question.text, required=True)
            elif question.question_type == Question.MULTIPLE_CHOICE:
                choices = [(option.option_text, option.option_text) for option in question.answeroption_set.all()]
                self.fields[field_name] = forms.ChoiceField(label=question.text, choices=choices,
                                                            widget=forms.RadioSelect, required=True)
            elif question.question_type == Question.SCALE:
                self.fields[field_name] = forms.IntegerField(
                    label=question.text,
                    widget=forms.NumberInput(attrs={'type': 'range',
                                                    'min': question.min_value,
                                                    'max': question.max_value}), required=True)
        # self.fields['captcha'] = ReCaptchaField()
