"""Админ-панель для приложения recipes."""
from django.contrib import admin
from admin_auto_filters.filters import AutocompleteFilter

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


class TagFilter(AutocompleteFilter):
    title = 'Тег'
    field_name = 'tags'


class AuthorFilter(AutocompleteFilter):
    title = 'Автор'
    field_name = 'author'


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

    list_display = ("name", "author",
                    "get_favorite_count", "get_shopping_cart_count")
    list_filter = (TagFilter, AuthorFilter)

    def get_queryset(self, request):
        """Метод для получения queryset с аннотациями."""
        return (
            super()
            .get_queryset(request)
            .select_related('author')
            .prefetch_related('tags', 'ingredients')
        )

    def get_favorite_count(self, obj):
        """Метод для получения количества добавлений в избранное."""
        return obj.favorited_by.count()

    get_favorite_count.short_description = "В избранном"

    def get_shopping_cart_count(self, obj):
        """Метод для получения количества добавлений в список покупок."""
        return obj.in_shopping_cart.count()

    get_shopping_cart_count.short_description = "В списке покупок"


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Админ-панель для ингредиентов в рецептах."""

    list_display = ("recipe", "ingredient", "amount")
    list_filter = ("recipe__author__username", "ingredient__name")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('recipe', 'ingredient')
        )


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Админ-панель для избранных рецептов."""

    list_display = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('user', 'recipe')
        )


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """Админ-панель для списка покупок."""

    list_display = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('user', 'recipe')
        )
