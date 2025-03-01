from django.urls import include, path
from rest_framework import routers

from api.views import IngredientViewSet, RecipeViewSet, TagViewSet
from user.urls import user_urlpatterns

router_v1 = routers.DefaultRouter()
router_v1.register('recipes', RecipeViewSet)
router_v1.register('tags', TagViewSet)
router_v1.register('ingredients', IngredientViewSet)

v1_patterns = [
    path('', include(router_v1.urls)),
    path('', include(user_urlpatterns)),
]

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(v1_patterns)),
]
