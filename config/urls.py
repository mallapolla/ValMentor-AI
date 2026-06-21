from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def health_check(request):
    return JsonResponse({"status": "healthy", "service": "ValMentor AI"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    
    # ValMentor Apps URLs
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('chat/', include('apps.chat.urls')),
    path('interviews/', include('apps.interviews.urls')),
    path('roadmaps/', include('apps.roadmaps.urls')),
    path('resume/', include('apps.resume.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('gamification/', include('apps.gamification.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
