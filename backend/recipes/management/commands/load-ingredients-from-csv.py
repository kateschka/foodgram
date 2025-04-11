"""Команда для загрузки ингредиентов из CSV файла."""
import csv
from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    """Команда для загрузки ингредиентов из CSV файла."""

    help = 'Load ingredients from CSV file'

    def handle(self, *args, **kwargs):
        """Метод для загрузки ингредиентов из CSV файла."""
        with open(
            f'{settings.BASE_DIR}/data/ingredients.csv',
            encoding='utf-8'
        ) as file:
            reader = csv.DictReader(file)
            Ingredient.objects.bulk_create(
                Ingredient(
                    name=row['name'],
                    measurement_unit=row['measurement_unit']
                )
                for row in reader
            )

        self.stdout.write(self.style.SUCCESS(
            'Ingredients loaded successfully'))
