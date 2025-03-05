import hashlib
from django.db.models import Sum

from recipes.models import RecipeIngredient
from foodgram.constants import LENGTH_SHORT_LINK
import pdb


def generate_short_code_from_url(url, length=LENGTH_SHORT_LINK):
    hash_object = hashlib.sha256(url.encode())
    return hash_object.hexdigest()[:length]


def get_base_url(request):
    """Формирует базовый URL из запроса."""
    return f'{request.scheme}://{request.get_host()}'


def create_shopping_list(user):
    ingredients_summary = (
        RecipeIngredient.objects
        .filter(recipe__shopping_carted=user)
        .values('ingredient__name', 'ingredient__measurement_unit')
        .annotate(total_amount=Sum('amount'))
        .order_by('ingredient__name')
    )
    shopping_list_text = 'Список покупок:\n\n'
    for name, data in ingredients_summary:
        shopping_list_text += (
            f"{name}: {data['amount']} {data['measurement_unit']}\n"
        )
    return shopping_list_text
