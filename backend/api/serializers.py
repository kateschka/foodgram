"""Сериализаторы для API."""
import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from users.models import Follow

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Поле для работы с изображениями в формате base64.

    Преобразует изображение из формата base64 в файл и обратно.
    Поддерживает загрузку изображений через API в формате data:image.
    """

    def to_internal_value(self, data):
        """Преобразует base64 строку в файл изображения.

        Args:
            data (str): Строка с изображением в формате base64.

        Returns:
            ContentFile: Файл изображения.
        """
        if isinstance(data, str) and data.startswith('data:image'):
            img_format, img_str = data.split(';base64,')
            ext = img_format.split('/')[-1]
            data = ContentFile(base64.b64decode(img_str), name='image.' + ext)
        return super().to_internal_value(data)

    def to_representation(self, instance):
        """Преобразует файл изображения в URL.

        Args:
            instance (ImageField): Поле с изображением.

        Returns:
            str: URL изображения или None, если изображение отсутствует.
        """
        if instance:
            return instance.url
        return None


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с тегами рецептов.

    Предоставляет основные поля тега: id, название и slug.
    Используется для отображения тегов в рецептах и при их создании.
    """

    class Meta:
        """Мета класс для сериализатора тегов."""

        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с ингредиентами.

    Предоставляет основные поля ингредиента: id, название и единицу измерения.
    Используется для отображения ингредиентов в рецептах и при их создании.
    """

    class Meta:
        """Мета класс для сериализатора ингредиентов."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientWithAmountSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения ингредиентов с количеством в рецепте.

    Расширяет базовый сериализатор ингредиентов, добавляя поле количества.
    Используется при отображении полной информации о рецепте.
    """

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        """Мета класс для сериализатора ингредиентов с количеством."""

        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания связи между рецептом и ингредиентами.

    Используется при создании и обновлении рецепта для указания
    необходимых ингредиентов и их количества.
    """

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )

    class Meta:
        """Мета класс для сериализатора связи рецепт-ингредиент."""

        model = RecipeIngredient
        fields = ('id', 'amount')


class UserSerializer(DjoserUserSerializer):
    """Сериализатор для работы с пользователями.

    Расширяет базовый сериализатор Djoser, добавляя:
    - Поле для проверки подписки на пользователя
    - Поддержку загрузки аватара в формате base64
    """

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta(DjoserUserSerializer.Meta):
        """Мета класс для сериализатора пользователей."""

        model = User
        fields = (
            'email', 'id', 'avatar', 'is_subscribed',
            'username', 'first_name', 'last_name'
        )

    def get_is_subscribed(self, obj):
        """Проверяет, подписан ли текущий пользователь на данного пользователя.

        Args:
            obj (User): Пользователь, на которого проверяется подписка.

        Returns:
            bool: True, если текущий пользователь подписан, иначе False.
        """
        return (
            self.context['request'].user.is_authenticated
            and self.context['request'].user.following.filter(
                followee=obj).exists()
        )


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для работы с аватаром пользователя.

    Предоставляет возможность загрузки и обновления аватара
    пользователя в формате base64.
    """

    avatar = Base64ImageField(required=False)

    class Meta:
        """Мета класс для сериализатора аватара."""

        model = User
        fields = ('avatar',)


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого отображения рецепта.

    Используется в списках избранного, корзины покупок и подписок.
    Содержит только основные поля: id, название, изображение и
    время приготовления.
    """

    class Meta:
        """Мета класс для краткого сериализатора рецепта."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для полного отображения рецепта.

    Предоставляет полную информацию о рецепте, включая:
    - Основные данные (название, описание, время приготовления)
    - Список ингредиентов с количествами
    - Теги
    - Информацию об авторе
    - Статусы (в избранном, в корзине)
    """

    ingredients = IngredientWithAmountSerializer(
        many=True,
        required=True,
        source='recipe_ingredients'
    )
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, required=True)
    image = Base64ImageField(required=False)
    is_favorited = serializers.BooleanField(default=False)
    is_in_shopping_cart = serializers.BooleanField(default=False)

    class Meta:
        """Мета класс для полного сериализатора рецепта."""

        model = Recipe
        fields = ('id', 'name', 'text', 'ingredients', 'tags', 'cooking_time',
                  'author', 'image', 'is_favorited', 'is_in_shopping_cart')
        read_only_fields = ('author',)


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецептов.

    Предоставляет функциональность для:
    - Создания новых рецептов
    - Обновления существующих рецептов
    - Валидации данных (уникальность тегов и ингредиентов)
    - Обработки связанных объектов (теги и ингредиенты)
    """

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        """Мета класс для сериализатора создания/обновления рецепта."""

        model = Recipe
        fields = ('id', 'name', 'text', 'ingredients',
                  'tags', 'cooking_time', 'image')
        read_only_fields = ('author',)

    @transaction.atomic
    def create(self, validated_data):
        """Создает новый рецепт с учетом связанных объектов.

        Args:
            validated_data (dict): Валидированные данные для создания рецепта.

        Returns:
            Recipe: Созданный рецепт.
        """
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(**validated_data)

        self._handle_related_objects(
            recipe, {'tags': tags, 'ingredients': ingredients})
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Обновляет существующий рецепт с учетом связанных объектов.

        Args:
            instance (Recipe): Рецепт для обновления.
            validated_data (dict): Валидированные данные для обновления.

        Returns:
            Recipe: Обновленный рецепт.
        """
        self._handle_related_objects(instance, validated_data)
        instance.save()
        return instance

    def to_representation(self, instance):
        """Преобразует рецепт в формат для отображения.

        Args:
            instance (Recipe): Рецепт для преобразования.

        Returns:
            dict: Данные рецепта в формате для отображения.
        """
        return RecipeSerializer(instance, context=self.context).data

    def validate(self, data):
        """Проверяет валидность данных рецепта.

        Args:
            data (dict): Данные для валидации.

        Returns:
            dict: Валидированные данные.

        Raises:
            ValidationError: Если данные не соответствуют требованиям.
        """
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError({
                'tags': 'Нужно выбрать хотя бы один тег'
            })

        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise serializers.ValidationError({
                    'tags': 'Теги должны быть уникальными'
                })
            tags_list.append(tag)

        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError({
                'ingredients': 'Нужно добавить хотя бы один ингредиент'
            })

        ingredients_list = []
        for ingredient in ingredients:
            if ingredient['ingredient'] in ingredients_list:
                raise serializers.ValidationError({
                    'ingredients': 'Ингредиенты должны быть уникальными'
                })
            ingredients_list.append(ingredient['ingredient'])

        return data

    def _handle_related_objects(self, recipe, validated_data):
        """Обрабатывает связанные объекты рецепта (теги и ингредиенты).

        Args:
            recipe (Recipe): Рецепт для обработки.
            validated_data (dict): Валидированные данные.
        """
        tags = validated_data.pop('tags', None)
        recipe.tags.clear()
        recipe.tags.set(tags)

        recipe.recipe_ingredients.all().delete()
        ingredients = validated_data.pop('ingredients', None)
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)


class FollowSerializer(UserSerializer):
    """Сериализатор для работы с подписками на пользователей.

    Расширяет UserSerializer, добавляя:
    - Список рецептов пользователя с учетом лимита
    - Количество рецептов пользователя (через аннотацию)
    """

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(default=0)

    class Meta(UserSerializer.Meta):
        """Мета класс для сериализатора подписок."""

        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')
        read_only_fields = fields

    def to_representation(self, instance):
        """Преобразует подписку в формат для отображения.

        Args:
            instance (Follow): Подписка для преобразования.

        Returns:
            dict: Данные подписки в формате для отображения.
        """
        if isinstance(instance, Follow):
            instance = instance.followee
        return super().to_representation(instance)

    def get_recipes(self, obj):
        """Получает список рецептов пользователя с учетом лимита.

        Args:
            obj (User/Follow): Пользователь или подписка.

        Returns:
            list: Список рецептов пользователя.
        """
        user = obj.followee if isinstance(obj, Follow) else obj
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit') if request else None
        recipes = user.recipes.all()
        if limit:
            recipes = recipes[:int(limit)]
        return [
            {
                'id': recipe.id,
                'name': recipe.name,
                'image': recipe.image.url if recipe.image else None,
                'cooking_time': recipe.cooking_time,
            }
            for recipe in recipes
        ]


class FollowCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписок на пользователей.

    Предоставляет функциональность для:
    - Создания новых подписок
    - Валидации данных (проверка на подписку на самого себя)
    """

    class Meta:
        """Мета класс для сериализатора создания подписок."""

        model = Follow
        fields = ('followee', 'follower')

    def validate(self, value):
        """Проверяет валидность данных подписки.

        Args:
            value (dict): Данные для валидации.

        Returns:
            dict: Валидированные данные.

        Raises:
            ValidationError: Если данные не соответствуют требованиям.
        """
        follower = value.get('follower')
        followee = value.get('followee')

        if follower == followee:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя'
            )

        if Follow.objects.filter(
            follower_id=follower,
            followee_id=followee
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя'
            )

        return value

    def to_representation(self, instance):
        """Преобразует подписку в формат для отображения.

        Args:
            instance (Follow): Подписка для преобразования.

        Returns:
            dict: Данные подписки в формате для отображения.
        """
        return FollowSerializer(instance, context=self.context).data


class BaseUserRecipeSerializer(serializers.ModelSerializer):
    """Базовый сериализатор для моделей, связывающих пользователя и рецепт.

    Предоставляет общую функциональность для создания и валидации
    связей между пользователями и рецептами. Автоматически устанавливает
    текущего пользователя и проверяет уникальность связей.
    """

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    recipe = serializers.PrimaryKeyRelatedField(queryset=Recipe.objects.all())

    class Meta:
        """Мета класс для базового сериализатора.

        Определяет поля для сериализации и устанавливает
        поле пользователя как только для чтения.
        """
        fields = ('user', 'recipe')
        read_only_fields = ('user',)

    def validate(self, data):
        """Проверяет валидность данных для создания связи.

        Args:
            data (dict): Данные для валидации.

        Returns:
            dict: Валидированные данные.

        Raises:
            ValidationError: Если связь уже существует.
        """
        if self.Meta.model.objects.filter(
            user=data['user'],
            recipe=data['recipe']
        ).exists():
            raise serializers.ValidationError(
                f'Рецепт уже добавлен в {self.Meta.model._meta.verbose_name}!'
            )
        return data

    def to_representation(self, instance):
        """Преобразует объект в формат для отображения.

        Args:
            instance: Объект для преобразования.

        Returns:
            dict: Данные рецепта в формате для отображения.
        """
        return RecipeShortSerializer(
            instance.recipe, context=self.context
        ).data


class FavoriteSerializer(BaseUserRecipeSerializer):
    """Сериализатор для избранных рецептов.

    Обеспечивает создание и валидацию связей между
    пользователями и их избранными рецептами.
    """

    class Meta(BaseUserRecipeSerializer.Meta):
        """Мета класс для сериализатора избранного.

        Определяет модель и наследует настройки полей
        от базового сериализатора.
        """
        model = Favorite


class ShoppingCartSerializer(BaseUserRecipeSerializer):
    """Сериализатор для списка покупок.

    Обеспечивает создание и валидацию связей между
    пользователями и рецептами в их списке покупок.
    """

    class Meta(BaseUserRecipeSerializer.Meta):
        """Мета класс для сериализатора корзины.

        Определяет модель и наследует настройки полей
        от базового сериализатора.
        """
        model = ShoppingCart
