from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.permissions import AdminPermission, UserAnonPermission
from foodgram import utiles
from foodgram.filters import RecipeFilter
from recipes.models import (Ingredient, Recipe, ShortLink, Tag)
from recipes.serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer,
)
from user.serializers import RecipeUserSerializer


class RecipeActionMixin:
    """Миксин для добавления/удаления рецептов в корзину и избранное."""

    def recipe_action(self, request, pk=None, related_name=None):
        """Общая логика для добавления/удаления в shopping_cart/favorite."""
        user = request.user
        target_recipe = get_object_or_404(Recipe, id=pk)
        related_manager = getattr(target_recipe, related_name)
        if request.method == 'POST':
            if related_manager.filter(id=user.id).exists():
                return Response(
                    {'error': 'Рецепт уже добавлен.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            related_manager.add(user)
            return Response(
                RecipeUserSerializer(
                    target_recipe, context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
            if not related_manager.filter(id=user.id).exists():
                return Response(
                    {'error': 'Рецепта нет в списке.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            related_manager.remove(user)
            return Response(
                RecipeUserSerializer(
                    target_recipe, context={'request': request}
                ).data,
                status=status.HTTP_204_NO_CONTENT
            )


class RecipeViewSet(viewsets.ModelViewSet, RecipeActionMixin):
    """Основной вьюсет для обработки действий с рецептами."""

    queryset = Recipe.objects.all()
    permission_classes = [
        UserAnonPermission | AdminPermission
    ]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def create(self, request, *args, **kwargs):
        """Создание рецепта с возвратом полного представления"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        recipe = serializer.instance
        return Response(
            RecipeReadSerializer(recipe, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        """Обновление рецепта с возвратом полного представления"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            RecipeReadSerializer(instance, context={'request': request}).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post', 'delete'], url_path='shopping_cart')
    def shopping_cart(self, request, pk=None):
        """Добавление рецепта в корзину."""
        return self.recipe_action(request, pk, related_name='shopping_carted')

    @action(detail=True, methods=['post', 'delete'], url_path='favorite')
    def favorite(self, request, pk=None):
        """Добавление рецепта в избраное."""
        return self.recipe_action(request, pk, related_name='favorited')

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def get_shopping_cart_file(self, request):
        """Метод получения файла со списком покупок."""
        user = request.user
        file = utiles.create_shopping_list(user)
        return FileResponse(
            file, as_attachment=True, filename='shopping_list.txt'
        )

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        """Метод получения короткой ссылки на рецепт."""
        recipe = get_object_or_404(Recipe, id=pk)
        base_url = utiles.get_base_url(request)
        original_url = request.build_absolute_uri(
            reverse('recipe-detail', kwargs={'pk': recipe.id})
        )
        shortlink, created = ShortLink.objects.get_or_create(
            original_url=recipe.id,
            short_code=utiles.generate_short_code_from_url(original_url)
        )
        short_url = f'{base_url}/s/{shortlink.short_code}'
        return Response({'short-link': short_url})


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для просмотра тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [
        UserAnonPermission | AdminPermission
    ]
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для просмотра ингридиентов."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [
        UserAnonPermission | AdminPermission
    ]
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('name',)
    pagination_class = None
