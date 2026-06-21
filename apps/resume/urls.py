from django.urls import path
from . import views

app_name = 'resume'

urlpatterns = [
    # Template views
    path('', views.resume_home, name='home'),
    path('status/<int:resume_id>/', views.resume_status, name='status'),
    
    # REST API
    path('api/upload/', views.APIResumeUploadView.as_view(), name='api_upload'),
]
