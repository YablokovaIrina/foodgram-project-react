import csv

from django.core.management.base import BaseCommand
from recipes.models import Ingredient


def load_ingredients():
    print('loading ingedients...')
    ingredients = []
    with open("./recipes/data/ingredients.csv", encoding="utf-8-sig") as file:
        reader = csv.reader(file)
        for row in reader:
            ingredient = Ingredient(
                name=row[0],
                measurement_unit=row[1],
            )
            ingredients.append(ingredient)
        Ingredient.objects.bulk_create(ingredients)
    print('ingredients loaded!')


class Command(BaseCommand):

    def handle(self, *args, **options):
        try:
            load_ingredients()
        except Exception as error:
            print(error)
