import random
import string
import base64
from djoser.serializers import UserSerializer as DjoserUserSerializer
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework import serializers
from django.db import transaction

from recipes.models import (Tag, Ingredient, Recipe,
                            RecipeIngredient, ShoppingCart, Favorite)
from users.models import Follow

User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Класс для преобразования изображения в base64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            img_format, img_str = data.split(';base64,')
            ext = img_format.split('/')[-1]
            data = ContentFile(base64.b64decode(img_str), name='image.' + ext)
        return super().to_internal_value(data)

    def to_representation(self, instance):
        if instance:
            return instance.url
        return None


class TagSerializer(serializers.ModelSerializer):
    """Сериалайзер для тегов."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """Сериалайзер для ингредиентов."""
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientWithAmountSerializer(serializers.ModelSerializer):
    """Сериалайзер для ингредиентов с указанием количества."""
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    """Сериалайзер для создания связи ингредиентов с рецептом."""
    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredient.objects.all(),
        source='ingredient'
    )
    amount = serializers.IntegerField(min_value=1)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class UserSerializer(DjoserUserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta(DjoserUserSerializer.Meta):
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
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = ('avatar',)


class RecipeSerializer(serializers.ModelSerializer):
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
        model = Recipe
        fields = ('id', 'name', 'text', 'ingredients', 'tags', 'cooking_time',
                  'author', 'image', 'is_favorited', 'is_in_shopping_cart')
        read_only_fields = ('author',)

    def get_is_favorited(self, obj):
        return (
            self.context['request'].user.is_authenticated
            and self.context['request'].user.favorites.filter(
                recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        return (
            self.context['request'].user.is_authenticated
            and self.context['request'].user.shopping_cart.filter(
                recipe=obj).exists()
        )


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    ingredients = RecipeIngredientCreateSerializer(many=True)
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'text', 'ingredients',
                  'tags', 'cooking_time', 'image')
        read_only_fields = ('author',)

    @transaction.atomic
    def create(self, validated_data):
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
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')

        instance = super().update(instance, validated_data)

        instance.tags.clear()
        instance.tags.set(tags)

        instance.ingredients.all().delete()
        recipe_ingredients = [
            RecipeIngredient(
                recipe=instance,
                ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data

    def validate_ingredients(self, value):
        ingredients_list = []
        for ingredient in value:
            ingredient_id = ingredient['ingredient'].id
            if not ingredient_id:
                raise serializers.ValidationError(
                    'Отсутствует id ингредиента'
                )
            if ingredient_id in ingredients_list:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться'
                )
            ingredients_list.append(ingredient_id)
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Нужно выбрать хотя бы один тег'
            )
        tags_list = []
        for tag in value:
            if tag in tags_list:
                raise serializers.ValidationError(
                    'Теги должны быть уникальными'
                )
            tags_list.append(tag)
        return value


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('id', 'recipe', 'user')

    def validate(self, value):
        if not Recipe.objects.filter(id=value.id).exists():
            raise serializers.ValidationError(
                'Рецепт не найден'
            )
        if ShoppingCart.objects.filter(user=self.context['request'].user,
                                       recipe=value.id).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в корзину'
            )
        return value

    def create(self, validated_data):
        return ShoppingCart.objects.create(**validated_data)

    def to_representation(self, instance):
        return {
            'id': instance.recipe.id,
            'name': instance.recipe.name,
            'image': instance.recipe.image.url,
            'cooking_time': instance.recipe.cooking_time,
        }


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ('id', 'recipe', 'user')

    def validate(self, value):
        if not Recipe.objects.filter(id=value.id).exists():
            raise serializers.ValidationError(
                'Рецепт не найден'
            )
        if Favorite.objects.filter(user=self.context['request'].user,
                                   recipe=value.id).exists():
            raise serializers.ValidationError(
                'Рецепт уже добавлен в избранное'
            )
        return value

    def create(self, validated_data):
        return Favorite.objects.create(**validated_data)

    def to_representation(self, instance):
        return {
            'id': instance.recipe.id,
            'name': instance.recipe.name,
            'image': instance.recipe.image.url,
            'cooking_time': instance.recipe.cooking_time,
        }


class FollowSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='followee.id')
    email = serializers.EmailField(source='followee.email')
    username = serializers.CharField(source='followee.username')
    first_name = serializers.CharField(source='followee.first_name')
    last_name = serializers.CharField(source='followee.last_name')
    avatar = serializers.ImageField(source='followee.avatar')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name',
                  'avatar', 'recipes', 'recipes_count', 'is_subscribed')

    def get_is_subscribed(self, obj):
        return Follow.objects.filter(
            follower=self.context['request'].user,
            followee=obj.followee
        ).exists()

    def get_recipes(self, obj):
        """
        Метод для получения рецептов подписчика
        с ограничением на количество.
        """
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit') if request else None
        recipes = obj.followee.recipes.all()
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
        return obj.followee.recipes.count()


class FollowCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('followee', 'follower')

    def validate(self, value):
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
        return FollowSerializer(instance, context=self.context).data
