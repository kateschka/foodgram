from django.urls import include, path
from rest_framework import routers

from .views import UserViewSet, TagViewSet, IngredientViewSet, RecipeViewSet

router = routers.DefaultRouter()
router.register(r'tags', TagViewSet)
router.register(r'ingredients', IngredientViewSet)
router.register(r'recipes', RecipeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'users/me/avatar/',
        UserViewSet.as_view({'put': 'set_avatar', 'delete': 'delete_avatar'})
    ),
]
