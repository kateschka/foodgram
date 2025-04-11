"""Админ-панель для приложения recipes."""
from django.contrib import admin

from .models import (Tag, Ingredient, Recipe,
                     RecipeIngredient, Favorite, ShoppingCart)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Админ-панель для тегов."""

    list_display = ("name", "slug")
    search_fields = ("name", "slug")


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """Админ-панель для ингредиентов."""

    list_display = ("name", "measurement_unit")
    search_fields = ("name",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админ-панель для рецептов."""

    list_display = ("name", "author")
    search_fields = ("name", "author__username")
    list_filter = ("tags",)

    def get_favorite_count(self, obj):
        """Метод для получения количества добавлений в избранное."""
        return obj.favorites.count()

    get_favorite_count.short_description = "В избранном"

    def get_shopping_cart_count(self, obj):
        """Метод для получения количества добавлений в список покупок."""
        return obj.shopping_cart.count()

    get_shopping_cart_count.short_description = "В списке покупок"


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Админ-панель для ингредиентов в рецептах."""

    list_display = ("recipe", "ingredient", "amount")
    search_fields = ("recipe__name", "ingredient__name")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админ-панель для избранных рецептов."""

    list_display = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админ-панель для списка покупок."""

    list_display = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")
