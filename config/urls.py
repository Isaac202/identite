from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404, handler500
#from rest_framework import permissions
#from drf_yasg.views import get_schema_view
#from drf_yasg import openapi
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


'''schema_view = get_schema_view(
   openapi.Info(
      title="VoucherManager API",
      default_version='v1',
      description="API para gestão de vouchers e clientes",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)
'''
def trigger_error(request):
    division_by_zero = 1 / 0

handler404 = 'base.views.handler404'
handler500 = 'base.views.handler500'
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('base.urls')),
    path('', include('dashboard.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('sentry-debug/', trigger_error),
    #path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    #path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)