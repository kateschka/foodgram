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
            reader = csv.reader(file)
            for row in reader:
                name, measurement_unit = row
                Ingredient.objects.get_or_create(
                    name=name, measurement_unit=measurement_unit)

        self.stdout.write(self.style.SUCCESS(
            'Ingredients loaded successfully'))
