
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.views.generic import TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html')),
    
    
    path('api/auth/', include('core.urls')),
    path('api/employee/', include('employee.urls')),
    
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls
    
    urlpatterns += debug_toolbar_urls()    
