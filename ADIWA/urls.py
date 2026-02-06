
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.views.generic import TemplateView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('core.urls')),
    path('api/employee/', include('employee.urls')),
    path('', TemplateView.as_view(template_name='index.html')),
]

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls
    
    urlpatterns += debug_toolbar_urls()    
