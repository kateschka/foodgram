import django_filters
from rest_framework import filters
from django.contrib.auth import get_user_model
from django_filters.rest_framework import FilterSet
from django.db.models import Case, When, Value, IntegerField, Q
from django.contrib.auth.models import User

from recipes.models import Tag, Recipe

User = get_user_model()


class IngredientSearchFilter(filters.SearchFilter):
    def filter_queryset(self, request, queryset, view):
        search_term = request.query_params.get('name')

        if not search_term:
            return queryset
        else:
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
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def filter_is_favorited(self, queryset, name, value):
        if value == '1' and self.request.user.is_authenticated:
            return queryset.filter(favorited_by__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(in_shopping_cart__user=self.request.user)
        return queryset
