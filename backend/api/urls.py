from django.urls import include, path
from djoser.views import UserViewSet
from rest_framework import routers

from api.views import (
    CustomUserViewSet,
    IngredientViewSet,
    RecipeViewSet,
    ListUserViewSet,
    TagViewSet
)


router_v1 = routers.DefaultRouter()
router_v1.register('recipes', RecipeViewSet)
router_v1.register('tags', TagViewSet)
router_v1.register('ingredients', IngredientViewSet)

user_urlpatterns = [
    path(
        'users/',
        ListUserViewSet.as_view({'get': 'list', 'post': 'create', }),
        name='user-create'
    ),
    path(
        'users/subscriptions/',
        CustomUserViewSet.as_view({'get': 'subscriptions'}),
        name='user-subscriptions'
    ),
    path(
        'users/<int:id>/',
        UserViewSet.as_view({'get': 'retrieve'}),
        name='user-detail'
    ),
    path(
        'users/<int:id>/subscribe/',
        CustomUserViewSet.as_view(
            {'post': 'subscribe', 'delete': 'unsubscribe'}
        ),
        name='user-subscribe'
    ),
    path(
        'users/me/',
        CustomUserViewSet.as_view({'get': 'me'}),
        name='user_me'
    ),
    path(
        'users/me/avatar/',
        CustomUserViewSet.as_view(
            {'put': 'update_avatar', 'delete': 'update_avatar'}
        ),
        name='user_me_avatar'
    ),
    path(
        'users/set_password/',
        UserViewSet.as_view({'post': 'set_password'}),
        name='set-password'
    ),
]

v1_patterns = [
    path('', include(router_v1.urls)),
    path('', include(user_urlpatterns)),
]

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(v1_patterns)),
]
