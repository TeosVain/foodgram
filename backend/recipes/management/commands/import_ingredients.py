import json
from django.core.management.base import BaseCommand
from recipes.models import Ingredient


class Command(BaseCommand):
    help = 'Загружает данные о продуктах из JSON файла в базу данных'

    def handle(self, *args, **kwargs):
        json_file_path = 'ingredients.json'
        with open(json_file_path, 'r', encoding='utf-8') as file:
            products_data = json.load(file)
        for product in products_data:
            Ingredient.objects.create(
                name=product['name'],
                measurement_unit=product['measurement_unit']
            )

        self.stdout.write(self.style.SUCCESS('Данные успешно загружены!'))
