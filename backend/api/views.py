from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import SetPasswordSerializer
from djoser.views import UserViewSet
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from recipes.models import (Favourites, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag,)
from users.models import Follow, User
from users.validators import validate_username

from .filters import IngredientSearchFilter, RecipesFilter
from .pagination import RecipesFollowsPagination
from .permissions import (AdminPermission, CurrentUserPermission,
                          ReadOnlyPermission,)
from .serializers import (FavouritesSerializer, FollowSerializer,
                          IngredientSerializer, RecipeSerializer,
                          RecipeWriteSerializer, ShoppingCartSerializer,
                          TagSerializer, UserFoodCreateSerializer,
                          UserFoodSerializer,)


class UsersViewSet(UserViewSet):

    def get_queryset(self):
        return User.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserFoodCreateSerializer
        if self.action == 'set_password':
            return SetPasswordSerializer
        return UserFoodSerializer

    def validate_username(self, value):
        return validate_username(value)


class FollowBaseViewSet(viewsets.GenericViewSet):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.context.get('request').user
        return user.follower.all()


class FollowGetViewSet(
    mixins.ListModelMixin,
    FollowBaseViewSet
):
    pagination_class = RecipesFollowsPagination


class FollowViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    FollowBaseViewSet
):

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['author_id'] = self.kwargs.get('user_id')
        return context

    def create(self, request, *args, **kwargs):
        author_id = self.kwargs.get('user_id')
        author = get_object_or_404(User, id=author_id)
        serializer = FollowSerializer(author)
        Follow.objects.create(
            user=request.user,
            author=author
        )
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        author_id = self.kwargs.get('id')
        author = get_object_or_404(User, id=author_id)
        get_object_or_404(
            Follow,
            user=request.user,
            author=author
        ).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AdminPermission | ReadOnlyPermission,)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AdminPermission | ReadOnlyPermission,)
    filter_backends = (IngredientSearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (
        AdminPermission | CurrentUserPermission | ReadOnlyPermission,
    )
    pagination_class = RecipesFollowsPagination
    filter_backends = (DjangoFilterBackend, )
    filterset_class = RecipesFilter

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeSerializer
        return RecipeWriteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        serializer = RecipeSerializer(
            instance=serializer.instance,
            context={'request': self.request}
        )
        return Response(
            serializer.data, status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        serializer = RecipeSerializer(
            instance=serializer.instance,
            context={'request': self.request}
        )
        return Response(
            serializer.data, status=status.HTTP_200_OK
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class FavouriteViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [IsAuthenticated]
    serializer_class = FavouritesSerializer

    def get_queryset(self, obj):
        user = self.context.get('request').user
        return obj.favorite_recipe.filter(user=user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['recipe_id'] = self.kwargs.get('recipe_id')
        return context

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        favorite_recipe = get_object_or_404(Recipe, id=recipe_id)
        Favourites.objects.create(
            user=request.user,
            favorite_recipe=favorite_recipe
        )
        serializer = FavouritesSerializer(favorite_recipe)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        favorite_recipe = get_object_or_404(Recipe, id=recipe_id)
        get_object_or_404(Favourites,
                          user=request.user,
                          favorite_recipe=favorite_recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [permissions.IsAuthenticated]
    queryset = ShoppingCart.objects.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['recipe_id'] = self.kwargs.get('recipe_id')
        return context

    def create(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        ShoppingCart.objects.create(
            user=request.user,
            recipe=recipe)
        serializer = ShoppingCartSerializer(recipe)
        return Response(data=serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        recipe_id = self.kwargs.get('recipe_id')
        recipe = get_object_or_404(Recipe, id=recipe_id)
        get_object_or_404(ShoppingCart,
                          user=request.user,
                          recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingListDownload(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.shopping_cart.all()

    def get(self, request):
        response = HttpResponse(content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return self._create_shopping_list(self.get_queryset(), response)

    def _create_shopping_list(self, response, request):
        shopping_cart = self.request.user.shopping_cart.all()
        shopping_list = {}
        response.write('Мой список продуктов:\n')
        for item in shopping_cart:
            ingredients_recipe = IngredientRecipe.objects.filter(
                recipe=item.recipe
            )
            for row in ingredients_recipe:
                ingredient = row.ingredient
                amount = row.amount
                if ingredient in shopping_list:
                    shopping_list[ingredient] += amount
                else:
                    shopping_list[ingredient] = amount
        for ingredient, amount in shopping_list.items():
            response.write(f'\n{ingredient.name}')
            response.write((f' ({ingredient.measurement_unit})'))
            response.write(f' - {amount}')
        return response
