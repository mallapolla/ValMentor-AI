from django.urls import path
from . import views

app_name = 'interviews'

urlpatterns = [
    path('', views.interview_home, name='home'),
    path('start/', views.start_interview, name='start'),
    path('<int:session_id>/', views.interview_session, name='session'),
    path('<int:session_id>/submit/', views.submit_answer, name='submit'),
    path('<int:session_id>/results/', views.interview_results, name='results'),
    
    # REST API
    path('api/<int:session_id>/', views.APIInterviewSessionView.as_view(), name='api_session'),
]
