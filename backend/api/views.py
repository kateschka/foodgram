"""Views для API."""
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import Favorite, Ingredient, Recipe, ShoppingCart, Tag
from users.models import Follow

from .filters import IngredientSearchFilter, RecipeFilter
from .pagination import PaginatorWithLimit
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    FollowCreateSerializer,
    FollowSerializer,
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeSerializer,
    RecipeShortSerializer,
    TagSerializer,
    UserAvatarSerializer,
    UserSerializer,
)

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    """Класс для работы с пользователями."""

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
        """Метод для создания подписки."""
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
        """Метод для удаления подписки."""
        followee = get_object_or_404(User, id=kwargs['id'])

        follow = Follow.objects.filter(
            follower=request.user,
            followee=followee
        ).first()

        if not follow:
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        follow.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        """Метод для получения списка подписок пользователя."""
        subscriptions = Follow.objects.filter(follower=request.user)
        page = self.paginate_queryset(subscriptions)
        if page is not None:
            serializer = FollowSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = FollowSerializer(
            subscriptions,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Класс для работы с тегами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Класс для работы с ингредиентами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Класс для работы с рецептами."""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = PaginatorWithLimit
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = RecipeFilter
    search_fields = ('name', 'author__username', 'tags__name')
    permission_classes = (IsOwnerOrReadOnly,)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, *args, **kwargs):
        """Метод для добавления и удаления рецепта из списка избранного."""
        recipe = self.get_object()
        if request.method == 'POST':
            return self.add_to(Favorite, request.user, recipe.id)
        else:
            return self.remove_from(Favorite, request.user, recipe.id)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, *args, **kwargs):
        """Метод для добавления и удаления рецепта из списка покупок."""
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
        short_link = f'{request.get_host()}/{recipe.short_link}/'
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
        url_path='short-link-redirect',
    )
    def short_link_redirect(self, request, short_link=None):
        """Перенаправление по короткой ссылке на рецепт."""
        recipe = get_object_or_404(Recipe, short_link=short_link)
        return HttpResponseRedirect(f'/recipes/{recipe.pk}/')

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Метод для скачивания списка покупок."""
        ingredients = (
            Recipe.objects.filter(in_shopping_cart__user=request.user)
            .values(
                'ingredients__name',
                'ingredients__measurement_unit'
            )
            .annotate(total_amount=Sum('recipeingredient__amount'))
            .order_by('ingredients__name')
        )

        shopping_list = ['Список покупок:\n\n']
        for ingredient in ingredients:
            shopping_list.append(
                f"- {ingredient['ingredients__name']} "
                f"({ingredient['ingredients__measurement_unit']}) — "
                f"{ingredient['total_amount']}\n"
            )

        response = HttpResponse(
            ''.join(shopping_list),
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    def get_permissions(self):
        """Метод для проверки прав доступа."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Метод для сохранения рецепта."""
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        """Метод для получения сериализатора."""
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return super().get_serializer_class()

    def add_to(self, model, user, pk):
        """Метод для проверки существования объекта и создания нового."""
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response({'detail': 'Рецепт уже добавлен!'},
                            status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(
            recipe, context={'request': self.request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_from(self, model, user, pk):
        """Метод для удаления объекта."""
        try:
            obj = get_object_or_404(model, user=user, recipe__id=pk)
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'detail': str(e)},
                            status=status.HTTP_400_BAD_REQUEST)
