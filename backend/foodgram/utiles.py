import hashlib

from recipes.models import Recipe
from foodgram.constants import LENGTH_SHORT_LINK


def generate_short_code_from_url(url, length=LENGTH_SHORT_LINK):
    hash_object = hashlib.sha256(url.encode())
    return hash_object.hexdigest()[:length]


def get_base_url(request):
    """Формирует базовый URL из запроса."""
    return f'{request.scheme}://{request.get_host()}'


def create_shopping_list(user):
    ingredients_summary = {}
    recipes = Recipe.objects.filter(shopping_carted=user)
    for recipe in recipes:
        recipe_ingredients = recipe.ingredients.through.objects.filter(
            recipe=recipe
        )
        for recipe_ingredient in recipe_ingredients:
            ingredient = recipe_ingredient.ingredient
            amount = recipe_ingredient.amount
            if ingredient.name in ingredients_summary:
                ingredients_summary[ingredient.name]['amount'] += amount
            else:
                ingredients_summary[ingredient.name] = {
                    'measurement_unit': ingredient.measurement_unit,
                    'amount': amount
                }
    shopping_list_text = 'Список покупок:\n\n'
    for name, data in ingredients_summary.items():
        shopping_list_text += (
            f"{name}: {data['amount']} {data['measurement_unit']}\n"
        )
    return shopping_list_text
