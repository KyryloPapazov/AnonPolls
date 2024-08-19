import base64
import os
from collections import Counter
from mimetypes import guess_type
from django.contrib import messages

from django.urls import reverse

from matplotlib import pyplot as plt
from django.http import HttpResponse, JsonResponse, Http404, HttpResponseRedirect
from django.views import View
from .utils import verify_recaptcha, validate_questions_data
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

from AnonPolls import settings
from common.views import TitleMixin
import json

from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView, ListView, FormView
from django.db.models import Q

from .forms import SurveyResponseForm
from .models import Survey, Question, AnswerOption, Response, QuestionLogic
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import pandas as pd


class PollsPrivateListView(TitleMixin, ListView):
    model = Survey
    template_name = 'polls/private_polls.html'
    context_object_name = 'Survey'  # Use plural for context_object_name for clarity
    paginate_by = 6
    title = 'Мої опитування'

    def get_queryset(self):
        query = self.request.GET.get('q')
        user = self.request.user
        if query:
            return Survey.objects.filter(Q(title__icontains=query) & Q(author=user))
        return Survey.objects.filter(author=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['authors'] = Survey.objects.filter(author=self.request.user)
        return context


class PollsListView(TitleMixin, ListView):
    model = Survey
    template_name = 'polls/polls.html'
    context_object_name = 'Survey'
    paginate_by = 6
    title = 'Публічні опитування'

    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Survey.objects.filter(Q(title__icontains=query))
        return Survey.objects.all()


class IndexView(TitleMixin, TemplateView):
    template_name = 'polls/index.html'
    title = 'SimpleAnonSurvey'


class CreateSurveyView(View):
    title = 'Створення опитувань'

    def get(self, request):
        return render(request, 'polls/create_polls.html', {'title': self.title,
                                                           'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY})

    def post(self, request):
        author = request.user
        title = request.POST.get('title')
        description = request.POST.get('description')
        show_author = request.POST.get('show_author') == 'true'
        survey_visibility = request.POST.get('survey_visibility')
        recaptcha_token = request.POST.get('recaptcha_token')

        errors = []

        # Verify reCAPTCHA
        if not verify_recaptcha(recaptcha_token):
            errors.append('Invalid reCAPTCHA. Please try again.')

        if not title:
            errors.append('Необхідно вказати назву.')
        if not survey_visibility:
            errors.append('Потрібна видимість огляду.')

        if errors:
            return render(request,
                          'polls/create_polls.html',
                          {'errors': errors, 'title': self.title,
                           'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY})

        survey = Survey(title=title,
                        description=description,
                        author=author,
                        show_author=show_author,
                        survey_visibility=survey_visibility)

        data = request.POST.get('questions_data')
        if not data:
            errors.append('Дані питань відсутні.')
            return render(request, 'polls/create_polls.html',
                          {'errors': errors, 'title': self.title,
                           'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY})

        try:
            questions = json.loads(data)
        except json.JSONDecodeError:
            errors.append('Недійсний формат даних запитань.')
            return render(request,
                          'polls/create_polls.html',
                          {'errors': errors, 'title': self.title,
                           'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY})

        if not questions:
            errors.append('Потрібно принаймні одне запитання.')
            return render(request,
                          'polls/create_polls.html',
                          {'errors': errors, 'title': self.title,
                           'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY})

        survey.save()

        for q in questions:
            question_text = q['text']
            question_type = q['question_type']
            options = q.get('options', [])
            if question_type == 'scale':
                if not options or len(options) != 2:
                    errors.append('Шкала запитань повинна мати мінімальне та максимальне значення.')
                    return render(request,
                                  'polls/create_polls.html',
                                  {'errors': errors, 'title': self.title,
                                   'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY})

                try:
                    min_value, max_value = int(options[0]), int(options[1])
                except ValueError:
                    errors.append('Мінімальне та максимальне значення повинні бути числовими.')
                    return render(request,
                                  'polls/create_polls.html',
                                  {'errors': errors, 'title': self.title,
                                   'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY})

                if min_value < -10000 or max_value > 10000:
                    errors.append('Мінімальне та максимальне значення повинні бути в діапазоні від -10000 до 10000.')
                    return render(request,
                                  'polls/create_polls.html',
                                  {'errors': errors, 'title': self.title,
                                   'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY})

                question = Question(text=question_text, question_type=question_type, survey=survey, min_value=min_value,
                                    max_value=max_value)
            else:
                question = Question(text=question_text, question_type=question_type, survey=survey)
            question.save()

            if question_type == 'multiple_choice':
                if not options:
                    errors.append('Питання з декількома відповідями повинні мати принаймні один варіант.')
                    return render(request,
                                  'polls/create_polls.html',
                                  {'errors': errors, 'title': self.title,
                                   'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY})
                for option_text in options:
                    answer_option = AnswerOption(question=question, option_text=option_text)
                    answer_option.save()

        return redirect('polls:index')


class EditSurveyView(View):
    def get(self, request, survey_slug):
        survey = get_object_or_404(Survey, slug=survey_slug)
        title = 'Редагування'
        questions = Question.objects.filter(survey=survey)
        return render(request, 'polls/edit_survey.html', {
            'survey': survey,
            'questions': questions,
            'title': title,
            'RECAPTCHA_PUBLIC_KEY': settings.RECAPTCHA_PUBLIC_KEY
        })

    def post(self, request, survey_slug):
        survey = get_object_or_404(Survey, slug=survey_slug)
        recaptcha_token = request.POST.get('recaptcha_token')

        if not verify_recaptcha(recaptcha_token):
            return JsonResponse({"error": "Недійсний reCAPTCHA. Будь ласка спробуйте ще раз."}, status=400)

        survey.title = request.POST.get('title')
        survey.save()

        questions_data = request.POST.get('questions_data')
        try:
            questions = json.loads(questions_data)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Недійсні дані JSON"}, status=400)

        is_valid, error_message = validate_questions_data(questions)
        if not is_valid:
            return JsonResponse({"error": error_message}, status=400)

        existing_questions = {q.id: q for q in Question.objects.filter(survey=survey)}
        processed_question_ids = set()

        for q in questions:
            question_text = q['text']
            question_type = q['question_type']
            question = None

            for existing_question in existing_questions.values():
                if existing_question.text == question_text and existing_question.question_type == question_type:
                    question = existing_question
                    processed_question_ids.add(question.id)
                    break

            if question:
                if question_type == 'scale':
                    min_value, max_value = q.get('options')
                    question.min_value = min_value
                    question.max_value = max_value
                question.save()
            else:
                if question_type == 'scale':
                    min_value, max_value = q.get('options')
                    question = Question(
                        text=question_text,
                        question_type=question_type,
                        survey=survey,
                        min_value=min_value,
                        max_value=max_value
                    )
                else:
                    question = Question(
                        text=question_text,
                        question_type=question_type,
                        survey=survey
                    )
                question.save()
                processed_question_ids.add(question.id)

            if question_type == 'multiple_choice':
                existing_options = {o.id: o for o in AnswerOption.objects.filter(question=question)}
                options = q.get('options')
                processed_option_ids = set()

                for option in options:
                    if isinstance(option, dict):
                        option_text = option['text']
                    else:
                        option_text = option

                    answer_option = None
                    for existing_option in existing_options.values():
                        if existing_option.option_text == option_text:
                            answer_option = existing_option
                            processed_option_ids.add(answer_option.id)
                            break

                    if answer_option:
                        answer_option.option_text = option_text
                        answer_option.save()
                    else:
                        answer_option = AnswerOption(question=question, option_text=option_text)
                        answer_option.save()
                        processed_option_ids.add(answer_option.id)

                for option_id in existing_options:
                    if option_id not in processed_option_ids:
                        existing_options[option_id].delete()

        for question_id in existing_questions:
            if question_id not in processed_question_ids:
                existing_questions[question_id].delete()

        return redirect('polls:survey_detail', survey_slug=survey.slug)


def delete_survey(request, survey_slug):
    survey = get_object_or_404(Survey, slug=survey_slug)
    questions = Question.objects.filter(survey=survey)
    if request.method == 'POST':
        survey.delete()
        return redirect('polls:index')
    return render(request, 'polls/survey_detail.html', {'survey': survey, 'questions': questions})


class SurveyDetailView(TitleMixin, TemplateView):
    model = Survey
    context_object_name = 'Survey'
    template_name = 'polls/survey_detail.html'
    title = 'Деталі'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        survey_slug = self.kwargs.get('survey_slug')
        survey = get_object_or_404(Survey, slug=survey_slug)
        questions = Question.objects.filter(survey=survey)
        context.update({
            'survey': survey,
            'questions': questions,
            'domain_name': self.request.get_host(),
            'this_user': self.request.user
        })
        return context


class SurveyResponseView(FormView):
    template_name = 'polls/respond_to_survey.html'
    form_class = SurveyResponseForm

    def dispatch(self, request, *args, **kwargs):
        self.survey = get_object_or_404(Survey, slug=self.kwargs['survey_slug'])
        self.respondent_identifier = request.unique_identifier

        if Response.objects.filter(survey_question__survey=self.survey,
                                   respondent_identifier=self.respondent_identifier).exists():
            messages.error(request, "Ви вже надали свою відповідь на це опитування!")
            return redirect('index')

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.survey = get_object_or_404(Survey, slug=self.kwargs['survey_slug'])
        questions = Question.objects.filter(survey=self.survey)
        kwargs['questions'] = questions
        return kwargs

    def form_valid(self, form):
        for key, value in form.cleaned_data.items():
            question_id = key.split('_')[1]
            question = get_object_or_404(Question, pk=question_id)
            answer = value
            response = Response(survey_question=question, answer=answer,
                                respondent_identifier=self.respondent_identifier)
            response.save()

            logic = QuestionLogic.objects.filter(question=question, trigger_answer=answer).first()
            if logic:
                current_question = logic.target_question
                break

        return redirect('polls:thank_you')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['survey'] = self.survey
        context['questions'] = Question.objects.filter(survey=self.survey)
        return context


def generate_line_chart(values, title):
    fig, ax = plt.subplots()
    ax.plot(range(1, len(values) + 1), values, marker='o')
    ax.set_title(title)
    ax.set_xlabel('Response Number')
    ax.set_ylabel('Scale Value')
    plt.xticks(rotation=45, ha='right')

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_png = buffer.getvalue()
    buffer.close()

    graphic = base64.b64encode(image_png)
    graphic = graphic.decode('utf-8')

    return graphic


plt.switch_backend('Agg')


def survey_statistics(request, survey_slug):
    survey = get_object_or_404(Survey, slug=survey_slug)
    title = 'Статистика'
    questions = survey.question_set.all()

    responses = Response.objects.filter(survey_question__survey=survey)

    data = []
    for response in responses:
        data.append({
            'question_id': response.survey_question.id,
            'question_text': response.survey_question.text,
            'question_type': response.survey_question.question_type,
            'answer': response.answer,
        })

    # Convert data to DataFrame
    df = pd.DataFrame(data)

    if df.empty:
        return render(request, 'polls/survey_statistics.html', {
            'survey': survey,
            'statistics': [],
            'all_answers': [],
            'pie_charts': {},
            'line_charts': {},
            'error': 'Не знайдено відповідей на це опитування.',
            'title': title
        })

    if 'question_text' not in df.columns or 'question_type' not in df.columns:
        return render(request, 'polls/survey_statistics.html', {
            'survey': survey,
            'statistics': [],
            'all_answers': [],
            'pie_charts': {},
            'line_charts': {},
            'error': 'Відсутні необхідні стовпці даних.',
            'title': title
        })

    # General statistics including question type and most popular answer
    stats = df.groupby(['question_text', 'question_type']).agg({
        'answer': ['count', pd.Series.mode]
    }).reset_index()
    stats.columns = ['question', 'question_type', 'total_responses', 'most_popular_answer']

    # Format the most popular answers properly
    stats['most_popular_answer'] = stats['most_popular_answer'].apply(
        lambda x: ', '.join(map(str, x)) if isinstance(x, list) else x)
    stats_dict = stats.to_dict(orient='records')

    # All answers statistics
    all_answers = df.groupby(['question_text', 'answer']).size().reset_index(name='count')
    all_answers_dict = all_answers.to_dict(orient='records')

    # Generate pie charts for multiple choice questions
    pie_charts = {}
    multiple_choice_questions = df[df['question_type'] == 'multiple_choice']['question_text'].unique()
    for question in multiple_choice_questions:
        question_data = df[df['question_text'] == question]
        answer_counts = question_data['answer'].value_counts()
        fig, ax = plt.subplots()
        ax.pie(answer_counts, labels=answer_counts.index, autopct='%1.1f%%',
               colors=plt.cm.Paired(range(len(answer_counts))))
        ax.set_title(f'{question}')
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close(fig)
        pie_charts[question] = base64.b64encode(buf.getvalue()).decode('utf-8')

    # Generate line charts for scale questions
    line_charts = {}
    scale_questions = df[df['question_type'] == 'scale']['question_text'].unique()
    for question in scale_questions:
        question_data = df[df['question_text'] == question]
        answer_values = question_data['answer'].astype(float).tolist()  # Ensure answers are treated as floats
        line_chart = generate_line_chart(answer_values, question)
        line_charts[question] = line_chart

    context = {
        'survey': survey,
        'statistics': stats_dict,
        'all_answers': all_answers_dict,
        'pie_charts': pie_charts,
        'line_charts': line_charts,
        'title': title,
    }
    return render(request, 'polls/survey_statistics.html', context)


class DownloadSurveyPDFView(View):
    def get(self, request, survey_slug):
        survey = get_object_or_404(Survey, slug=survey_slug)
        questions = survey.question_set.all()

        pdfmetrics.registerFont(TTFont('DejaVuSans', 'static/vendor/fontawesome/DejaVuSans.ttf'))
        pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'static/vendor/fontawesome/DejaVuSans-Bold.ttf'))

        # Fetch responses
        responses = Response.objects.filter(survey_question__survey=survey)

        data = []
        for response in responses:
            data.append({
                'question_id': response.survey_question.id,
                'question_text': response.survey_question.text,
                'question_type': response.survey_question.question_type,
                'answer': response.answer,
            })

        df = pd.DataFrame(data)

        # Group by question_text and aggregate answers
        grouped = df.groupby(['question_text', 'question_type'])['answer'].apply(list).reset_index()

        # Create PDF
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)

        # Set font for the title
        p.setFont('DejaVuSans-Bold', 16)
        title = f"Статистика відповідей для: {survey.title}"
        title_width = p.stringWidth(title, 'DejaVuSans-Bold', 16)
        start_position = (letter[0] - title_width) / 2
        p.drawString(start_position, 750, title)

        # Set font for questions
        p.setFont('DejaVuSans-Bold', 16)
        y = 720
        for index, row in grouped.iterrows():
            question = row['question_text']
            question_type = row['question_type']
            answers = row['answer']

            p.drawString(100, y, f"Question: {question}")
            p.setFont('DejaVuSans', 12)
            y -= 20

            for answer in answers:
                if y < 50:  # Check for page overflow
                    p.showPage()
                    p.setFont('DejaVuSans', 14)
                    y = 750
                p.drawString(140, y, f"- {answer}")
                y -= 20

            if question_type == 'scale':
                # Calculate the average for scale questions
                numeric_answers = [int(ans) for ans in answers if ans.isdigit()]
                if numeric_answers:
                    average = sum(numeric_answers) / len(numeric_answers)
                    p.drawString(140, y, f"Середнє значення: {average:.2f}")
                else:
                    p.drawString(140, y, "Середнє значення: N/A")
                y -= 20
            else:
                # Calculate the most frequent answer for other types of questions
                answer_counts = Counter(answers)
                most_common_answer, most_common_count = answer_counts.most_common(1)[0]
                percentage = (most_common_count / len(answers)) * 100
                p.drawString(140, y, f"Найчастіше зстрічається: {most_common_answer} ({percentage:.2f}%)")
                y -= 20

            y -= 30  # Space between questions

            p.setFont('DejaVuSans-Bold', 16)

        p.save()
        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{survey.slug}_statistics.pdf"'
        return response


class DownloadSurveyExcelView(View):
    def get(self, request, survey_slug):
        survey = get_object_or_404(Survey, slug=survey_slug)
        questions = survey.question_set.all()

        # Fetch responses
        responses = Response.objects.filter(survey_question__survey=survey)

        data = []
        for response in responses:
            data.append({
                'question_id': response.survey_question.id,
                'question_text': response.survey_question.text,
                'question_type': response.survey_question.question_type,
                'answer': response.answer,
            })

        df = pd.DataFrame(data)

        # Group by question_text and aggregate answers
        grouped = df.groupby(['question_text', 'question_type'])['answer'].apply(list).reset_index()

        # Prepare data for the summary sheet
        summary_data = []
        detailed_data = []
        for index, row in grouped.iterrows():
            question = row['question_text']
            question_type = row['question_type']
            answers = row['answer']

            if question_type == 'scale':
                numeric_answers = [int(ans) for ans in answers if ans.isdigit()]
                average = sum(numeric_answers) / len(numeric_answers) if numeric_answers else 'N/A'
                details = f"Average: {average:.2f}" if numeric_answers else "Average: N/A"
            else:
                answer_counts = Counter(answers)
                most_common_answer, most_common_count = answer_counts.most_common(1)[0]
                percentage = (most_common_count / len(answers)) * 100
                details = f"Most Common: {most_common_answer} ({percentage:.2f}%)"

            summary_data.append({
                'Question': question,
                'Type': question_type,
                'Details': details,
                'Answers': None  # Placeholder for the hyperlink
            })

            for answer in answers:
                detailed_data.append({
                    'Question': question,
                    'Answer': answer
                })

        summary_df = pd.DataFrame(summary_data)
        detailed_df = pd.DataFrame(detailed_data)

        # Create an Excel file
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            summary_df.to_excel(writer, index=False, sheet_name='Summary')
            detailed_df.to_excel(writer, index=False, sheet_name='Detailed Answers')

            # Format the Summary sheet
            workbook = writer.book
            summary_worksheet = writer.sheets['Summary']
            detailed_worksheet = writer.sheets['Detailed Answers']

            for col_num, value in enumerate(summary_df.columns.values):
                summary_worksheet.write(0, col_num, value)
                column_len = summary_df[value].astype(str).str.len().max()
                column_len = max(column_len, len(value)) + 2
                summary_worksheet.set_column(col_num, col_num, column_len)

            for col_num, value in enumerate(detailed_df.columns.values):
                detailed_worksheet.write(0, col_num, value)
                column_len = detailed_df[value].astype(str).str.len().max()
                column_len = max(column_len, len(value)) + 2
                detailed_worksheet.set_column(col_num, col_num, column_len)

            # Add hyperlinks to the summary sheet
            for row_num, question in enumerate(summary_df['Question'], start=1):
                link = f"internal:'Detailed Answers'!A{detailed_df[detailed_df['Question'] == question].index[0] + 2}"
                summary_worksheet.write_url(row_num, 3, link, string='See detailed answers')

        buffer.seek(0)

        response = HttpResponse(buffer, content_type='application/xlsx')
        response['Content-Disposition'] = f'attachment; filename="{survey.slug}_statistics.xlsx"'
        return response


class DownloadFileView(View):
    def get(self, request, filename):
        file_path = os.path.join(settings.MEDIA_ROOT, filename)
        if os.path.exists(file_path):
            content_type, _ = guess_type(file_path)
            if not content_type:
                content_type = 'application/octet-stream'
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type=content_type)
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
        raise Http404


def thank_you(request):
    return render(request, 'polls/thank_you.html')
