from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404, handler500
from django.urls import path

def trigger_error(request):
    division_by_zero = 1 / 0

handler404 = 'base.views.handler404'
handler500 = 'base.views.handler500'
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('base.urls')),
    path('sentry-debug/', trigger_error),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)