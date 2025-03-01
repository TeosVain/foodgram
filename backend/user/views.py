from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser import views
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from foodgram.constants import (
    DEFAULT_PAGINATOR_LIMIT,
    ACTION_LIST_USER_VIEWSET
)
from user.serializers import (
    AvatarSerializer, SubscribeUserSerializer, RecipeUserSerializer
)

User = get_user_model()


class ListUserViewSet(views.UserViewSet):

    def get_queryset(self):
        """Возвращаем всех пользователей, если запрашивается список"""
        queryset = User.objects.all()
        return queryset


class CustomUserViewSet(views.UserViewSet):

    def get_permissions(self):
        if self.action in ACTION_LIST_USER_VIEWSET:
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(
        detail=False,
        methods=["get"],
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
        target_user = get_object_or_404(User, id=id)
        if user == target_user:
            return Response(
                {'error': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if target_user in user.subscriptions.all():
            return Response(
                {'error': 'Вы уже подписаны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.subscriptions.add(target_user)
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
        methods=["delete"],
        permission_classes=[IsAuthenticated]
    )
    def unsubscribe(self, request, id=None):
        """Отписаться от пользователя"""
        user = request.user
        target_user = get_object_or_404(User, id=id)
        if target_user not in user.subscriptions.all():
            return Response(
                {'error': 'Вы не подписаны'},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.subscriptions.remove(target_user)
        return Response(
            {'detail': 'Вы отписались'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['put', 'delete'])
    def update_avatar(self, request, *args, **kwargs):
        user = request.user
        serializer = AvatarSerializer(user, data=request.data)
        if request.method == 'PUT':
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
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
