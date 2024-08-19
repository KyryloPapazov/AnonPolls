from django.contrib.auth.decorators import login_required
from django.urls import path

from polls.utils import user_is_author
from polls.views import (PollsListView, CreateSurveyView, SurveyResponseView,
                         delete_survey, SurveyDetailView, EditSurveyView, thank_you,
                         survey_statistics, PollsPrivateListView, DownloadSurveyExcelView,
                         DownloadSurveyPDFView, DownloadFileView)
from django.conf.urls.static import static
from django.conf import settings

app_name = 'polls'
#

urlpatterns = [
    path('', PollsListView.as_view(), name='index'),
    path('private/', login_required(PollsPrivateListView.as_view()), name='private'),
    path('create/', login_required(CreateSurveyView.as_view()), name='create_survey'),
    path('detail/<slug:survey_slug>/', SurveyDetailView.as_view(), name='survey_detail'),
    path('edit/<slug:survey_slug>/', user_is_author(EditSurveyView.as_view()), name='edit_survey'),
    path('delete/<slug:survey_slug>/', user_is_author(delete_survey), name='delete_survey'),
    path('response/<slug:survey_slug>/', SurveyResponseView.as_view(), name='respond_to_survey'),
    path('<slug:survey_slug>/statistics/', user_is_author(survey_statistics), name='survey_statistics'),
    path('<slug:survey_slug>/statistics//', user_is_author(DownloadSurveyPDFView.as_view()),
         name='download_survey_pdf'),
    path('<slug:survey_slug>/statistics///', user_is_author(DownloadSurveyExcelView.as_view()),
         name='download_survey_excel'),
    path('download/<str:filename>/', DownloadFileView.as_view(), name='download_file'),
    path('thank/', thank_you, name='thank_you'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
