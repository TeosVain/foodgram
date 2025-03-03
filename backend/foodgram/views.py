from django.shortcuts import get_object_or_404, redirect

from recipes.models import ShortLink


def short_link_redirect(request, short_code):
    """
    Перенаправление с короткой ссылки на оригинальный URL.
    """
    short_link = get_object_or_404(ShortLink, short_code=short_code)
    return redirect(f'http://158.160.6.136:8000/recipes/{short_link.original_url}')
