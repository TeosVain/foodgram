from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser import views
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from api.filters import RecipeFilter, CustomPageNumberPaginator
from api.permissions import AdminPermission, UserAnonPermission
from api.serializers import (
    AvatarSerializer,
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    RecipeUserSerializer,
    SubscribeUserSerializer,
    SubscriptionSerializer,
    TagSerializer,
)
from api import utiles
from foodgram.constants import (
    DEFAULT_PAGINATOR_LIMIT,
    ACTION_LIST_USER_VIEWSET
)
from recipes.models import (Ingredient, Recipe, ShortLink, Tag)

User = get_user_model()


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
    pagination_class = CustomPageNumberPaginator
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
            original_recipe_id=recipe.id,
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


def short_link_redirect(request, short_code):
    """
    Перенаправление с короткой ссылки на оригинальный URL.
    """
    short_link = get_object_or_404(ShortLink, short_code=short_code)
    return redirect(
        f'https://kittygramteos.ru/recipes/{short_link.original_recipe_id}'
    )


class ListUserViewSet(views.UserViewSet):

    def get_queryset(self):
        """Возвращаем всех пользователей, если запрашивается список"""
        return User.objects.all()


class CustomUserViewSet(views.UserViewSet):

    def get_permissions(self):
        if self.action in ACTION_LIST_USER_VIEWSET:
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Получить список всех подписок пользователя с лимитом на рецепты"""
        subscriptions = request.user.subscriptions.all()
        paginator = LimitOffsetPagination()
        paginator.default_limit = DEFAULT_PAGINATOR_LIMIT
        result_page = paginator.paginate_queryset(subscriptions, request)
        recipes_limit = int(
            request.query_params.get('recipes_limit', DEFAULT_PAGINATOR_LIMIT)
        )
        users_data = []
        for user in result_page:
            user_data = SubscribeUserSerializer(
                user, context={'request': request}
            ).data
            recipes = user.recipes.all()
            recipe_paginator = LimitOffsetPagination()
            recipe_paginator.default_limit = recipes_limit
            recipe_page = recipe_paginator.paginate_queryset(recipes, request)
            user_data['recipes'] = RecipeUserSerializer(
                recipe_page, context={'request': request}, many=True
            ).data
            users_data.append(user_data)
        return paginator.get_paginated_response(users_data)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        user = request.user
        data = {'target_user_id': id}
        serializer = SubscriptionSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        target_user = serializer.save()
        recipes_limit = int(
            request.query_params.get('recipes_limit', DEFAULT_PAGINATOR_LIMIT)
        )
        user_data = SubscribeUserSerializer(
            user, context={'request': request}
        ).data
        recipes = target_user.recipes.all()
        paginator = LimitOffsetPagination()
        paginator.default_limit = recipes_limit
        recipe_page = paginator.paginate_queryset(recipes, request)
        user_data['recipes'] = RecipeUserSerializer(
            recipe_page, context={'request': request}, many=True
        ).data
        return Response(user_data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['delete'],
        permission_classes=[IsAuthenticated]
    )
    def unsubscribe(self, request, id=None):
        """Отписаться от пользователя"""
        user = request.user
        target_user = get_object_or_404(User, id=id)
        if not user.subscriptions.filter(id=target_user.id).exists():
            return Response(
                {'error': 'Вы не подписаны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.subscriptions.remove(target_user)
        return Response(
            {'detail': 'Вы отписались!'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['put', 'delete'])
    def update_avatar(self, request, *args, **kwargs):
        user = request.user
        serializer = AvatarSerializer(user, data=request.data)
        if request.method == 'PUT':
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        if request.method == 'DELETE':
            user.avatar.delete(save=True)
            return Response(
                {'avatar': None},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'error': 'Method not allowed'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )
