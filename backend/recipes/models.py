from django.db import models
from django.contrib.auth import get_user_model
from backend.constants import (
    MAX_TAG_NAME_LENGTH,
    MAX_TAG_SLUG_LENGTH,
    MAX_INGREDIENT_NAME_LENGTH,
    MAX_INGREDIENT_MEASUREMENT_UNIT_LENGTH,
    MAX_RECIPE_NAME_LENGTH
)

User = get_user_model()


class Tag(models.Model):
    name = models.CharField(unique=True, max_length=MAX_TAG_NAME_LENGTH)
    slug = models.SlugField(unique=True, max_length=MAX_TAG_SLUG_LENGTH)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField(unique=True, max_length=MAX_INGREDIENT_NAME_LENGTH)
    measurement_unit = models.CharField(
        max_length=MAX_INGREDIENT_MEASUREMENT_UNIT_LENGTH)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    name = models.CharField(max_length=MAX_RECIPE_NAME_LENGTH)
    text = models.TextField()
    ingredients = models.ManyToManyField(
        Ingredient, through='RecipeIngredient')
    tags = models.ManyToManyField(Tag)
    cooking_time = models.PositiveIntegerField()
    is_favorited = models.BooleanField(default=False)
    is_in_shopping_cart = models.BooleanField(default=False)
    image = models.ImageField(upload_to='recipes/')

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['recipe', 'ingredient'],
                name='unique_recipe_ingredient'
            )
        ]
