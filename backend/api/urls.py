from django.urls import include, path
from .views import UserViewSet

urlpatterns = [
    path('users/', UserViewSet.as_view({'get': 'list'})),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
