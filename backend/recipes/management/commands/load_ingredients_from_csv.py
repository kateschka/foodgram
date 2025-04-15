"""Команда для загрузки ингредиентов из CSV файла."""
import csv

from django.core.management.base import BaseCommand

from recipes.models import Ingredient


class Command(BaseCommand):
    """Команда для загрузки ингредиентов из CSV файла."""

    help = 'Load ingredients from CSV file'

    def handle(self, *args, **options):
        """Метод для загрузки ингредиентов из CSV файла."""
        csv_file = 'data/ingredients.csv'

        try:
            with open(csv_file, encoding='utf-8') as file:
                reader = csv.reader(file)

                ingredients_to_create = [
                    Ingredient(
                        name=row[0],
                        measurement_unit=row[1]
                    )
                    for row in reader
                ]

                Ingredient.objects.bulk_create(ingredients_to_create)

                self.stdout.write(self.style.SUCCESS(
                    'Ingredients loaded successfully'
                ))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(
                f'File {csv_file} not found'
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Error loading ingredients: {str(e)}'
            ))
