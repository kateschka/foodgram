"""Админ-панель для приложения users."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import User, Follow


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Админ-панель для пользователей."""

    search_fields = ("email", "username")


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Админ-панель для подписок."""

    list_display = ("follower", "followee")
    search_fields = ("follower__username", "followee__username")
