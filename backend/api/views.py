"""Views для API."""
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from rest_framework import filters
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from djoser.views import UserViewSet as DjoserUserViewSet

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from recipes.models import Favorite, ShoppingCart, Tag, Ingredient, Recipe
from users.models import Follow
from .serializers import (
    RecipeCreateUpdateSerializer, TagSerializer,
    IngredientSerializer, RecipeSerializer,
    UserSerializer, UserAvatarSerializer,
    FavoriteSerializer, ShoppingCartSerializer,
    FollowSerializer, FollowCreateSerializer
)
from .permissions import IsOwnerOrReadOnly
from .filters import IngredientSearchFilter

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    serializer_class = UserSerializer

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Получение данных текущего пользователя."""
        return super().me(request)

    @action(
        detail=False,
        methods=['put'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated])
    def update_avatar(self, request):
        """Обновление аватара пользователя."""
        user = request.user
        if request.data.get('avatar'):
            serializer = UserAvatarSerializer(
                user,
                data=request.data,
                partial=True,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {'detail': 'Поле avatar не заполнено'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @update_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление аватара пользователя."""
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, *args, **kwargs):
        followee = get_object_or_404(User, id=kwargs['id'])
        follower = get_object_or_404(User, id=request.user.id)
        serializer = FollowCreateSerializer(
            data={'follower': follower.id, 'followee': followee.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, *args, **kwargs):
        followee = get_object_or_404(User, id=kwargs['id'])
        follow = get_object_or_404(Follow, follower=request.user,
                                   followee=followee)
        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name', 'author__username', 'tags__name')
    permission_classes = (IsOwnerOrReadOnly,)

    @action(
        detail=True,
        methods=['post', 'delete'],
    )
    def favorite(self, request, *args, **kwargs):
        """Метод для добавления и удаления рецепта из списка избранного"""
        recipe = self.get_object()
        if request.method == 'POST':
            return self.add_to(Favorite, request.user, recipe.id)
        else:
            return self.remove_from(Favorite, request.user, recipe.id)

    @action(
        detail=True,
        methods=['post', 'delete'],
    )
    def shopping_cart(self, request, *args, **kwargs):
        """Метод для добавления и удаления рецепта из списка покупок"""
        recipe = self.get_object()
        if request.method == 'POST':
            return self.add_to(ShoppingCart, request.user, recipe.id)
        else:
            return self.remove_from(ShoppingCart, request.user, recipe.id)

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
    )
    def get_link(self, request, *args, **kwargs):
        """Метод для получения короткой ссылки на рецепт."""
        recipe = get_object_or_404(Recipe, id=self.kwargs['pk'])
        short_link = recipe.short_link
        return Response({'short_link': short_link}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
    )
    def download_shopping_cart(self, request):
        """Метод для скачивания списка покупок."""
        shopping_cart = ShoppingCart.objects.filter(user=request.user)
        shopping_cart_items = []
        for item in shopping_cart:
            shopping_cart_items.append(item.recipe.ingredients.all())
        return Response(shopping_cart_items, status=status.HTTP_200_OK)

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return super().get_serializer_class()

    def add_to(self, model, user, pk):
        """Метод для проверки существования объекта и создания нового"""
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response({'errors': 'Рецепт уже добавлен!'},
                            status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_from(self, model, user, pk):
        """Метод для удаления объекта"""
        obj = get_object_or_404(model, user=user, recipe__id=pk)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def short_link_redirect(self, request, short_link=None):
        """Перенаправление по короткой ссылке на рецепт."""
        recipe = get_object_or_404(Recipe, short_link=short_link)
        return HttpResponseRedirect(f'/recipes/{recipe.pk}/')
