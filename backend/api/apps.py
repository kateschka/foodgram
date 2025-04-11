"""Конфигурация для API."""
from django.apps import AppConfig


class ApiConfig(AppConfig):
    """Конфигурация для API."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
