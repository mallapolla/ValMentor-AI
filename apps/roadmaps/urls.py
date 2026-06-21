from django.urls import path
from . import views

app_name = 'roadmaps'

urlpatterns = [
    # Template views
    path('', views.roadmap_list, name='list'),
    path('generate/', views.generate_custom_roadmap, name='generate'),
    path('<slug:slug>/', views.roadmap_detail, name='detail'),
    path('enroll/<int:roadmap_id>/', views.enroll_roadmap, name='enroll'),
    path('milestone/<int:user_roadmap_id>/<int:milestone_id>/', views.complete_milestone, name='complete_milestone'),
    
    # REST API
    path('api/list/', views.APIRoadmapListView.as_view(), name='api_list'),
]
