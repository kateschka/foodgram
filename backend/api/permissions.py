"""Настройки прав доступа для API."""
from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):
    """Права доступа для владельца или только для чтения."""

    def has_object_permission(self, request, view, obj):
        """Метод для проверки прав доступа."""
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return obj.author == request.user
