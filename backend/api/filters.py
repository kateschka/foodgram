from rest_framework import filters
from django.db.models import Case, When, Value, IntegerField, Q


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
