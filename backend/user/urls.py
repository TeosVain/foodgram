from django.urls import path
from djoser.views import UserViewSet

from api import views


user_urlpatterns = [
    path(
        'users/',
        views.ListUserViewSet.as_view({'get': 'list', 'post': 'create', }),
        name='user-create'
    ),
    path(
        'users/subscriptions/',
        views.CustomUserViewSet.as_view({'get': 'subscriptions'}),
        name='user-subscriptions'
    ),
    path(
        'users/<int:id>/',
        UserViewSet.as_view({'get': 'retrieve'}),
        name='user-detail'
    ),
    path(
        'users/<int:id>/subscribe/',
        views.CustomUserViewSet.as_view(
            {'post': 'subscribe', 'delete': 'unsubscribe'}
        ),
        name='user-subscribe'
    ),
    path(
        'users/me/',
        views.CustomUserViewSet.as_view({'get': 'me'}),
        name='user_me'
    ),
    path(
        'users/me/avatar/',
        views.CustomUserViewSet.as_view(
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
