"""Модуль с настройками URL-ов для проекта."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from api.views import RecipeViewSet

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('<str:short_link>/',
         RecipeViewSet.as_view({'get': 'short_link_redirect'})),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
