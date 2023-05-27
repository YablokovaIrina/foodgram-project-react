from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (FavouriteViewSet, FollowGetViewSet, FollowViewSet,
                    IngredientViewSet, RecipeViewSet, ShoppingCartViewSet,
                    ShoppingListDownload, TagViewSet, UsersViewSet,)

router = DefaultRouter()

router.register('users', UsersViewSet, basename='users')
router.register('tags', TagViewSet, basename='tags')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register(
    r'recipes/(?P<recipe_id>\d+)/favorite',
    FavouriteViewSet,
    basename='favorite'
)
router.register(
    r'recipes/(?P<recipe_id>\d+)/shopping_cart',
    ShoppingCartViewSet,
    basename='shopping_cart'
)


urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path(
        'recipes/download_shopping_cart/',
        ShoppingListDownload.as_view()
    ),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
]
