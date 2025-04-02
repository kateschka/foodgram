import csv
from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Load ingredients from CSV file'

    def handle(self, *args, **kwargs):
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
