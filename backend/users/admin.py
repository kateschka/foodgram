"""Админ-панель для приложения users."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from admin_auto_filters.filters import AutocompleteFilter
from users.models import Follow, User


class FollowerFilter(AutocompleteFilter):
    title = 'Подписчик'
    field_name = 'follower'


class FolloweeFilter(AutocompleteFilter):
    title = 'Подписка'
    field_name = 'followee'


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Админ-панель для пользователей."""

    search_fields = ("email", "username", "first_name", "last_name")


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Админ-панель для подписок."""

    list_display = ("follower", "followee")
    search_fields = ("follower__username", "followee__username")
    list_filter = (FollowerFilter, FolloweeFilter)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related('follower', 'followee')
        )
