"""Сериализаторы для API."""
import base64

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from django.shortcuts import get_object_or_404
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers, status
from rest_framework.response import Response

from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from users.models import Follow

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Класс для преобразования изображения в base64."""

    def to_internal_value(self, data):
        """Метод для преобразования изображения в base64."""
        if isinstance(data, str) and data.startswith('data:image'):
            img_format, img_str = data.split(';base64,')
            ext = img_format.split('/')[-1]
            data = ContentFile(base64.b64decode(img_str), name='image.' + ext)
        return super().to_internal_value(data)

    def to_representation(self, instance):
        """Метод для представления изображения."""
        if instance:
            return instance.url
        return None


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        """Мета класс для сериализатора."""

        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        """Мета класс для сериализатора."""

        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientWithAmountSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов с указанием количества."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        """Мета класс для сериализатора."""

        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания связи ингредиентов с рецептом."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        """Мета класс для сериализатора."""

        model = RecipeIngredient
        fields = ('id', 'amount')


class UserSerializer(DjoserUserSerializer):
    """Сериализатор для пользователей."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta(DjoserUserSerializer.Meta):
        """Мета класс для сериализатора."""

        model = get_user_model()
        fields = (
            'email', 'id', 'avatar', 'is_subscribed',
            'username', 'first_name', 'last_name'
        )

    def get_is_subscribed(self, obj):
        """Метод для проверки подписки на пользователя."""
        return (
            self.context['request'].user.is_authenticated
            and self.context['request'].user.following.filter(
                followee=obj).exists()
        )


class UserAvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для аватара пользователя."""

    avatar = Base64ImageField(required=False)

    class Meta:
        """Мета класс для сериализатора."""

        model = User
        fields = ('avatar',)


class RecipeShortSerializer(serializers.ModelSerializer):
    """Сериализатор для краткого отображения рецепта."""

    class Meta:
        """Мета класс для сериализатора."""

        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения рецепта."""

    ingredients = IngredientWithAmountSerializer(
        many=True,
        required=True,
        source='recipeingredient_set'
    )
    author = UserSerializer(read_only=True)
    tags = TagSerializer(many=True, required=True)
    image = Base64ImageField(required=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        """Мета класс для сериализатора."""

        model = Recipe
        fields = ('id', 'name', 'text', 'ingredients', 'tags', 'cooking_time',
                  'author', 'image', 'is_favorited', 'is_in_shopping_cart')
        read_only_fields = ('author',)

    def get_is_favorited(self, obj):
        """Метод для проверки наличия рецепта в избранном."""
        return (
            self.context['request'].user.is_authenticated
            and self.context['request'].user.favorites.filter(
                recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Метод для проверки наличия рецепта в списке покупок."""
        return (
            self.context['request'].user.is_authenticated
            and self.context['request'].user.shopping_cart.filter(
                recipe=obj).exists()
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания и обновления рецепта."""

    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        """Мета класс для сериализатора."""

        model = Recipe
        fields = ('id', 'name', 'text', 'ingredients',
                  'tags', 'cooking_time', 'image')
        read_only_fields = ('author',)

    @transaction.atomic
    def create(self, validated_data):
        """Метод для создания рецепта."""
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)

        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        """Метод для обновления рецепта."""
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)

        if tags is not None:
            instance.tags.clear()
            instance.tags.set(tags)

        if ingredients is not None:
            instance.recipeingredient_set.all().delete()
            recipe_ingredients = [
                RecipeIngredient(
                    recipe=instance,
                    ingredient=ingredient['ingredient'],
                    amount=ingredient['amount']
                )
                for ingredient in ingredients
            ]
            RecipeIngredient.objects.bulk_create(recipe_ingredients)

        instance.save()
        return instance

    def to_representation(self, instance):
        """Метод для представления рецепта."""
        return RecipeSerializer(instance, context=self.context).data

    def validate(self, data):
        """Метод для проверки валидности данных."""
        author = self.context['request'].user
        name = data.get('name')

        if Recipe.objects.filter(author=author, name=name).exists():
            raise serializers.ValidationError({
                'name': 'У вас уже есть рецепт с таким названием'
            })

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
                'ingredients': 'Нужно выбрать хотя бы один ингредиент'
            })

        ingredients_list = []
        for ingredient in ingredients:
            ingredient_id = ingredient['ingredient'].id
            if not ingredient_id:
                raise serializers.ValidationError({
                    'ingredients': 'Отсутствует id ингредиента'
                })
            if ingredient_id in ingredients_list:
                raise serializers.ValidationError({
                    'ingredients': 'Ингредиенты не должны повторяться'
                })
            ingredients_list.append(ingredient_id)

        return data


class FollowSerializer(UserSerializer):
    """Сериализатор для подписок."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        """Мета класс для сериализатора."""

        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')
        read_only_fields = fields

    def to_representation(self, instance):
        """Метод для представления подписки."""
        if isinstance(instance, Follow):
            instance = instance.followee
        return super().to_representation(instance)

    def get_recipes(self, obj):
        """Метод для получения рецептов пользователя с учетом лимита."""
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

    def get_recipes_count(self, obj):
        """Метод для получения количества рецептов пользователя."""
        user = obj.followee if isinstance(obj, Follow) else obj
        return user.recipes.count()


class FollowCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписки."""

    class Meta:
        """Мета класс для сериализатора."""

        model = Follow
        fields = ('followee', 'follower')

    def validate(self, value):
        """Метод для проверки валидности данных."""
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
        """Метод для представления подписки."""
        return FollowSerializer(instance, context=self.context).data

    def add_to(self, model, user, pk):
        """Метод для проверки существования объекта и создания нового."""
        if model.objects.filter(user=user, recipe__id=pk).exists():
            return Response({'errors': 'Рецепт уже добавлен!'},
                            status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        model.objects.create(user=user, recipe=recipe)
        serializer = RecipeShortSerializer(
            recipe, context={'request': self.request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)
