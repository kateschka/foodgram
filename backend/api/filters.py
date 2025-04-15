"""Фильтры для API."""
import django_filters
from django.contrib.auth import get_user_model
from django.db.models import Case, IntegerField, Q, Value, When
from rest_framework import filters

from recipes.models import Recipe

User = get_user_model()


class IngredientSearchFilter(filters.SearchFilter):
    """Фильтр для поиска ингредиентов."""

    def filter_queryset(self, request, queryset, view):
        """Метод для фильтрации ингредиентов."""
        search_term = request.query_params.get('name')

        if not search_term:
            return queryset

        search_term = search_term.lower()

        starts_with = Q(name__istartswith=search_term)
        contains = Q(name__icontains=search_term)

        return queryset.filter(starts_with | contains).annotate(
            sort_order=Case(
                When(name__istartswith=search_term, then=Value(1)),
                When(name__icontains=search_term, then=Value(2)),
                default=Value(3),
                output_field=IntegerField(),
            )
        ).order_by('sort_order', 'name')


class RecipeFilter(django_filters.FilterSet):
    """Фильтр для рецептов."""

    author = django_filters.ModelChoiceFilter(
        queryset=User.objects.all(),
        field_name='author'
    )
    tags = django_filters.AllValuesMultipleFilter(
        field_name='tags__slug',
    )
    is_favorited = django_filters.CharFilter(
        method='filter_is_favorited'
    )
    is_in_shopping_cart = django_filters.CharFilter(
        method='filter_is_in_shopping_cart'
    )

    class Meta:
        """Мета класс для фильтра."""

        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        """Метод для фильтрации рецептов по избранному."""
        if value == '1' and self.request.user.is_authenticated:
            return queryset.filter(favorited_by__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Метод для фильтрации рецептов по списку покупок."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(in_shopping_cart__user=self.request.user)
        return queryset
