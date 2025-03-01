import django_filters

from recipes.models import Recipe, Tag


class RecipeFilter(django_filters.FilterSet):
    """Кастомный фильтр для рецептов."""

    name = django_filters.CharFilter(lookup_expr='icontains')
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
        conjoined=False
    )
    author = django_filters.NumberFilter()
    is_favorited = django_filters.NumberFilter(
        field_name='favorited', method='filter_is_favorited'
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        field_name='shopping_carted', method='filter_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = [
            'name',
            'tags',
            'author',
            'is_in_shopping_cart',
            'is_favorited'
        ]

    def filter_is_favorited(self, queryset, name, value):
        """Фильтр избранных рецептов для текущего пользователя"""
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset
        if value:
            return queryset.filter(favorited=user)
        return queryset.exclude(favorited=user)

    def filter_is_in_shopping_cart(self, queryset, name, value):
        """Фильтр рецептов, добавленных в корзину покупок"""
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value else queryset
        if value:
            return queryset.filter(shopping_carted=user)
        return queryset.exclude(shopping_carted=user)
