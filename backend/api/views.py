"""Views для API."""
from django.contrib.auth import get_user_model
from django.db.models import Count, Exists, OuterRef, Sum
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
    FavoriteSerializer,
    FollowCreateSerializer,
    FollowSerializer,
    IngredientSerializer,
    RecipeCreateUpdateSerializer,
    RecipeSerializer,
    ShoppingCartSerializer,
    TagSerializer,
    UserAvatarSerializer,
    UserSerializer,
)

User = get_user_model()


class UserViewSet(DjoserUserViewSet):
    """ViewSet для управления пользователями.

    Предоставляет функциональность для:
    - Регистрации и аутентификации пользователей
    - Управления профилем пользователя
    - Работы с аватаром
    - Управления подписками на других пользователей
    """

    serializer_class = UserSerializer

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def me(self, request):
        """Получение данных текущего пользователя.

        Returns:
            Response: Данные текущего пользователя в формате JSON.
        """
        return super().me(request)

    @action(
        detail=False,
        methods=['put'],
        url_path='me/avatar',
        permission_classes=[IsAuthenticated])
    def update_avatar(self, request):
        """Обновление аватара пользователя.

        Args:
            request: Запрос с новым изображением аватара.

        Returns:
            Response: Обновленные данные пользователя или сообщение об ошибке.
        """
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

        return Response(
            {'detail': 'Поле avatar не заполнено'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @update_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление аватара пользователя.

        Returns:
            Response: Пустой ответ со статусом 204 при успешном удалении.
        """
        user = request.user
        if user.avatar:
            user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, *args, **kwargs):
        """Создание подписки на пользователя.

        Args:
            request: Запрос с данными для создания подписки.
            kwargs: Дополнительные параметры, включая ID пользователя.

        Returns:
            Response: Данные созданной подписки или сообщение об ошибке.
        """
        followee = get_object_or_404(User, id=kwargs['id'])

        serializer = FollowCreateSerializer(
            data={'follower': request.user.id, 'followee': followee.id},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def unsubscribe(self, request, *args, **kwargs):
        """Удаление подписки на пользователя.

        Args:
            request: Запрос на удаление подписки.
            kwargs: Дополнительные параметры, включая ID пользователя.

        Returns:
            Response: Пустой ответ при успешном удалении или
            сообщение об ошибке.
        """
        deleted_count, _ = Follow.objects.filter(
            follower=request.user,
            followee_id=kwargs['id']
        ).delete()
        if not deleted_count:
            return Response(
                {'detail': 'Ошибка при удалении подписки'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        """Получение списка подписок пользователя.

        Args:
            request: Запрос на получение списка подписок.

        Returns:
            Response: Пагинированный список подписок с данными пользователей.
        """
        subscriptions = Follow.objects.filter(
            follower=request.user
        ).select_related('followee').annotate(
            recipes_count=Count('followee__recipes')
        )
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
    """ViewSet для работы с тегами рецептов.

    Предоставляет функциональность для:
    - Получения списка всех тегов
    - Получения детальной информации о теге
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для работы с ингредиентами.

    Предоставляет функциональность для:
    - Получения списка всех ингредиентов
    - Поиска ингредиентов по названию
    - Получения детальной информации об ингредиенте
    """

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с рецептами.

    Предоставляет полный CRUD функционал для рецептов:
    - Создание, чтение, обновление и удаление рецептов
    - Фильтрация и поиск рецептов
    - Управление избранными рецептами
    - Управление списком покупок
    - Генерация коротких ссылок
    - Скачивание списка покупок
    """

    serializer_class = RecipeSerializer
    pagination_class = PaginatorWithLimit
    filter_backends = (DjangoFilterBackend, filters.SearchFilter)
    filterset_class = RecipeFilter
    search_fields = ('name', 'author__username', 'tags__name')
    permission_classes = (IsOwnerOrReadOnly,)

    def get_queryset(self):
        """Получение queryset с аннотациями для текущего пользователя.

        Добавляет аннотации:
        - is_favorited: находится ли рецепт в избранном
        - is_in_shopping_cart: находится ли рецепт в списке покупок

        Returns:
            QuerySet: Оптимизированный queryset с аннотациями.
        """
        queryset = Recipe.objects.select_related('author').prefetch_related(
            'tags', 'ingredients'
        ).all()
        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=self.request.user,
                        recipe=OuterRef('pk')
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=self.request.user,
                        recipe=OuterRef('pk')
                    )
                )
            )
        return queryset

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def favorite(self, request, *args, **kwargs):
        """Управление избранными рецептами.

        Args:
            request: Запрос на добавление/удаление из избранного.
            kwargs: Дополнительные параметры, включая ID рецепта.

        Returns:
            Response: Данные рецепта при добавлении или пустой
            ответ при удалении.
        """
        if request.method == 'POST':
            return self.add_to(Favorite, request.user, self.kwargs['pk'])

        return self.remove_from(Favorite, request.user, self.kwargs['pk'])

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=(IsAuthenticated,)
    )
    def shopping_cart(self, request, *args, **kwargs):
        """Управление списком покупок.

        Args:
            request: Запрос на добавление/удаление из списка покупок.
            kwargs: Дополнительные параметры, включая ID рецепта.

        Returns:
            Response: Данные рецепта при добавлении или пустой
            ответ при удалении.
        """
        if request.method == 'POST':
            return self.add_to(
                ShoppingCart, request.user, self.kwargs['pk'])

        return self.remove_from(
            ShoppingCart, request.user, self.kwargs['pk'])

    @action(
        detail=True,
        methods=['get'],
        url_path='get-link',
    )
    def get_link(self, request, *args, **kwargs):
        """Получение короткой ссылки на рецепт.

        Args:
            request: Запрос на получение короткой ссылки.
            kwargs: Дополнительные параметры, включая ID рецепта.

        Returns:
            Response: Короткая ссылка на рецепт.
        """
        recipe = get_object_or_404(Recipe, id=self.kwargs['pk'])
        short_link = f'{request.get_host()}/{recipe.short_link}/'
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=['get'],
        url_path='short-link-redirect',
    )
    def short_link_redirect(self, request, short_link=None):
        """Перенаправление по короткой ссылке на рецепт.

        Args:
            request: Запрос с короткой ссылкой.
            short_link: Короткая ссылка на рецепт.

        Returns:
            HttpResponseRedirect: Перенаправление на страницу рецепта.
        """
        recipe = get_object_or_404(Recipe, short_link=short_link)
        return HttpResponseRedirect(f'/recipes/{recipe.pk}/')

    def _generate_shopping_list(self, user):
        """Генерация текста списка покупок для пользователя.

        Args:
            user: Пользователь, для которого генерируется список.

        Returns:
            str: Текст списка покупок в формате plain text.
        """
        ingredients = (
            Recipe.objects.filter(in_shopping_cart__user=user)
            .values(
                'ingredients__name',
                'ingredients__measurement_unit'
            )
            .annotate(total_amount=Sum('recipe_ingredients__amount'))
            .order_by('ingredients__name')
        )

        shopping_list = ['Список покупок:\n\n']
        for ingredient in ingredients:
            shopping_list.append(
                f"- {ingredient['ingredients__name']} "
                f"({ingredient['ingredients__measurement_unit']}) — "
                f"{ingredient['total_amount']}\n"
            )

        return ''.join(shopping_list)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок в формате текстового файла.

        Args:
            request: Запрос на скачивание списка покупок.

        Returns:
            HttpResponse: Текстовый файл со списком покупок.
        """
        shopping_list_text = self._generate_shopping_list(request.user)

        response = HttpResponse(
            shopping_list_text,
            content_type='text/plain; charset=utf-8'
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response

    def get_permissions(self):
        """Получение списка разрешений для текущего действия.

        Returns:
            list: Список классов разрешений.
        """
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Сохранение нового рецепта.

        Args:
            serializer: Сериализатор с данными рецепта.
        """
        serializer.save(author=self.request.user)

    def get_serializer_class(self):
        """Получение класса сериализатора для текущего действия.

        Returns:
            Serializer: Класс сериализатора.
        """
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        return super().get_serializer_class()

    def add_to(self, model, user, pk):
        """Добавление рецепта в избранное или список покупок.

        Args:
            model: Модель (Favorite или ShoppingCart).
            user: Пользователь, добавляющий рецепт.
            pk: ID рецепта.

        Returns:
            Response: Данные добавленного рецепта.
        """
        recipe = get_object_or_404(Recipe, id=pk)
        serializer_class = (
            FavoriteSerializer if model == Favorite
            else ShoppingCartSerializer
        )
        serializer = serializer_class(
            data={'recipe': recipe.id},
            context={'request': self.request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_from(self, model, user, pk):
        """Удаление рецепта из избранного или списка покупок.

        Args:
            model: Модель (Favorite или ShoppingCart).
            user: Пользователь, удаляющий рецепт.
            pk: ID рецепта.

        Returns:
            Response: Пустой ответ при успешном удалении или
            сообщение об ошибке.
        """
        deleted_count, _ = model.objects.filter(
            user=user, recipe__id=pk
        ).delete()
        if not deleted_count:
            return Response(
                {'detail': 'Ошибка при удалении рецепта'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
