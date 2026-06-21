from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    # Template Views
    path('', views.chat_home, name='home'),
    path('new/', views.create_conversation, name='new_conversation'),
    path('<int:conversation_id>/send/', views.send_message, name='send_message'),
    
    # REST API views
    path('api/conversations/', views.APIConversationListCreateView.as_view(), name='api_conversations'),
    path('api/conversations/<int:conversation_id>/send/', views.APIMessageSendView.as_view(), name='api_send_message'),
]
