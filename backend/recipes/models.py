import random
import string
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator

from backend.constants import (
    MAX_TAG_NAME_LENGTH,
    MAX_TAG_SLUG_LENGTH,
    MAX_INGREDIENT_NAME_LENGTH,
    MAX_INGREDIENT_MEASUREMENT_UNIT_LENGTH,
    MAX_RECIPE_NAME_LENGTH,
    MAX_SHORT_LINK_LENGTH
)

User = get_user_model()


class Tag(models.Model):
    name = models.CharField('Имя тега', unique=True,
                            max_length=MAX_TAG_NAME_LENGTH)
    slug = models.SlugField('Ссылка на тег', unique=True,
                            max_length=MAX_TAG_SLUG_LENGTH)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(
        'Название ингредиента',
        unique=True,
        max_length=MAX_INGREDIENT_NAME_LENGTH)
    measurement_unit = models.CharField(
        'Единица измерения ингредиента',
        max_length=MAX_INGREDIENT_MEASUREMENT_UNIT_LENGTH)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return f'{self.name}, {self.measurement_unit}.'


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=200,
        verbose_name='Название'
    )
    text = models.TextField(verbose_name='Описание рецепта')
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient')
    tags = models.ManyToManyField(
        Tag, verbose_name='Теги', related_name='recipes')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время приготовления',
        validators=[MinValueValidator(
            1, 'Минимальное время приготовления - 1 минута')])
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipes/', blank=True, null=True)
    short_link = models.CharField(
        'Короткая ссылка',
        max_length=MAX_SHORT_LINK_LENGTH,
        unique=True,
        blank=True,
        null=True
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'name'],
                name='unique_recipe_author_name'
            )
        ]

    def create_short_link(self):
        """Метод для создания короткой ссылки"""
        while not self.short_link:
            short_link = ''.join(random.choices(
                string.ascii_letters + string.digits, k=6))
            if not Recipe.objects.filter(short_link=short_link).exists():
                self.short_link = short_link
                break
        return short_link

    def save(self, *args, **kwargs):
        if not self.short_link:
            self.create_short_link()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1)]
    )

    def __str__(self):
        return f'{self.recipe.name} - {self.ingredient.name}'

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]


class Favorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name='Избранный рецепт'
    )

    def __str__(self):
        return f'{self.user.username} добавил "{self.recipe.name}" в избранное'

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Рецепт в корзине'
    )

    def __str__(self):
        return f'{self.user.username} добавил "{self.recipe.name}" в корзину'

    class Meta:
        ordering = ('-id',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
