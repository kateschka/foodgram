"""Модели для приложения recipes."""
import random
import string

from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from backend.constants import (
    MAX_INGREDIENT_MEASUREMENT_UNIT_LENGTH,
    MAX_INGREDIENT_NAME_LENGTH,
    MAX_RECIPE_NAME_LENGTH,
    MAX_SHORT_LINK_LENGTH,
    MAX_TAG_NAME_LENGTH,
    MAX_TAG_SLUG_LENGTH,
)

User = get_user_model()


class Tag(models.Model):
    """Модель тега для категоризации рецептов.

    Теги позволяют группировать рецепты по различным признакам (например,
    завтрак, обед, ужин, вегетарианское, быстрое приготовление и т.д.).
    Каждый тег имеет уникальное имя и slug для URL.
    """

    name = models.CharField('Имя тега', unique=True,
                            max_length=MAX_TAG_NAME_LENGTH)
    slug = models.SlugField('Ссылка на тег', unique=True,
                            max_length=MAX_TAG_SLUG_LENGTH)

    class Meta:
        """Мета класс для тега.

        Определяет порядок сортировки по имени, а также русскоязычные названия
        для единственного и множественного числа.
        """

        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        """Строковое представление тега."""
        return self.name


class Ingredient(models.Model):
    """Модель ингредиента для рецептов.

    Хранит информацию о продуктах, используемых в рецептах, включая их название
    и единицу измерения. Каждый ингредиент имеет уникальное название для
    предотвращения дублирования в базе данных.
    """

    name = models.CharField(
        'Название ингредиента',
        unique=True,
        max_length=MAX_INGREDIENT_NAME_LENGTH)
    measurement_unit = models.CharField(
        'Единица измерения ингредиента',
        max_length=MAX_INGREDIENT_MEASUREMENT_UNIT_LENGTH)

    class Meta:
        """Мета класс для ингредиента.

        Определяет порядок сортировки по имени, а также русскоязычные названия
        для единственного и множественного числа.
        """

        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        """
        Строковое представление ингредиента в формате
        'Название, единица измерения'.
        """
        return f'{self.name}, {self.measurement_unit}.'


class Recipe(models.Model):
    """Модель рецепта - основная сущность приложения.

    Содержит полную информацию о рецепте: название, описание, время
    приготовления, изображение, автора, список ингредиентов с их
    количеством и теги. Поддерживает короткие ссылки для быстрого
    доступа к рецепту.
    """

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=MAX_RECIPE_NAME_LENGTH,
        verbose_name='Название',
    )
    text = models.TextField(verbose_name='Описание рецепта')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='RecipeIngredient',
        related_name='recipes'
    )
    tags = models.ManyToManyField(
        Tag, verbose_name='Теги', related_name='recipes')
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления',
        validators=[
            MinValueValidator(1, 'Минимальное время приготовления - 1 минута'),
            MaxValueValidator(
                300, 'Максимальное время приготовления - 300 минут')
        ])
    image = models.ImageField(
        verbose_name='Изображение',
        upload_to='recipes/', blank=True)
    short_link = models.CharField(
        'Короткая ссылка',
        max_length=MAX_SHORT_LINK_LENGTH,
        unique=True,
        blank=True,
        null=True
    )

    class Meta:
        """Мета класс для рецепта.

        Определяет порядок сортировки по id в обратном порядке, а также
        русскоязычные названия для единственного и множественного числа.
        Устанавливает ограничение на уникальность комбинации автора и
        названия рецепта.
        """

        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['author', 'name'],
                name='unique_recipe_author_name'
            )
        ]

    def __str__(self):
        """Строковое представление рецепта."""
        return self.name

    def save(self, *args, **kwargs):
        """Сохраняет рецепт в базе данных.

        Автоматически генерирует короткую ссылку, если она не была
        создана ранее.
        """
        if not self.short_link:
            self.create_short_link()
        super().save(*args, **kwargs)

    def create_short_link(self):
        """Создает уникальную короткую ссылку для рецепта.

        Генерирует случайную строку длиной 6 символов, состоящую из
        букв и цифр. Проверяет уникальность сгенерированной ссылки в
        базе данных.
        """
        while not self.short_link:
            short_link = ''.join(random.choices(
                string.ascii_letters + string.digits, k=6))
            if not Recipe.objects.filter(short_link=short_link).exists():
                self.short_link = short_link
                break
        return short_link


class RecipeIngredient(models.Model):
    """Промежуточная модель для связи рецептов и ингредиентов.

    Хранит информацию о количестве каждого ингредиента в конкретном
    рецепте. Обеспечивает уникальность комбинации рецепта и
    ингредиента.
    """

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='ingredient_recipes'
    )
    amount = models.PositiveSmallIntegerField(
        verbose_name='Количество',
        validators=[MinValueValidator(1), MaxValueValidator(5000)]
    )

    class Meta:
        """Мета класс для ингредиента в рецепте.

        Определяет порядок сортировки по рецепту и ингредиенту, а также
        устанавливает ограничение на уникальность комбинации рецепта и
        ингредиента.
        """

        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]
        ordering = ('recipe', 'ingredient')

    def __str__(self):
        """Строковое представление ингредиента в рецепте."""
        return f'{self.recipe.name} - {self.ingredient.name}'


class Favorite(models.Model):
    """Модель для хранения избранных рецептов пользователей.

    Позволяет пользователям сохранять понравившиеся рецепты для
    быстрого доступа. Каждый пользователь может добавить рецепт в
    избранное только один раз.
    """

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

    class Meta:
        """Мета класс для избранного.

        Определяет порядок сортировки по id в обратном порядке, а также
        русскоязычные названия для единственного и множественного числа.
        Устанавливает ограничение на уникальность комбинации пользователя
        и рецепта.
        """

        ordering = ('-id',)
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        """Строковое представление избранного."""
        return f'{self.user.username} добавил "{self.recipe.name}" в избранное'


class ShoppingCart(models.Model):
    """Модель для хранения рецептов в списке покупок пользователей.

    Позволяет пользователям добавлять рецепты в список покупок для
    удобного формирования списка необходимых ингредиентов. Каждый
    пользователь может добавить рецепт в список покупок только один раз.
    """

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

    class Meta:
        """Мета класс для корзины.

        Определяет порядок сортировки по id в обратном порядке, а также
        русскоязычные названия для единственного и множественного числа.
        Устанавливает ограничение на уникальность комбинации пользователя
        и рецепта.
        """

        ordering = ('-id',)
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_cart'
            )
        ]

    def __str__(self):
        """Строковое представление корзины."""
        return f'{self.user.username} добавил "{self.recipe.name}" в корзину'
