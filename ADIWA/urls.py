
from django.contrib import admin
from django.urls import path,include
from django.conf import settings


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('core.urls')),
    path('api/employee/', include('employee.urls'))
]

if settings.DEBUG:
    from debug_toolbar.toolbar import debug_toolbar_urls
    
    urlpatterns += debug_toolbar_urls()    
