from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response

from rest_framework import mixins, permissions, status, views, viewsets
from rest_framework.views import APIView
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from djoser.serializers import SetPasswordSerializer

from recipes.models import (Favourites, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag)
from users.models import User, Follow

from .filters import IngredientSearchFilter, RecipesFilter
from .pagination import RecipesFollowsPagination
from .permissions import (AdminPermission, CurrentUserPermission,
                          ReadOnlyPermission)
from .serializers import (UserFoodCreateSerializer,
                          UserFoodSerializer, FavouritesSerializer,
                          FollowSerializer, IngredientSerializer,
                          RecipeSerializer, RecipeWriteSerializer,
                          ShoppingCartSerializer, TagSerializer)
from users.validators import validate_username


class UsersViewSet(views.UserViewSet):

    def get_queryset(self):
        return User.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserFoodCreateSerializer
        elif self.action == 'set_password':
            return SetPasswordSerializer
        return UserFoodSerializer

    def validate_username(self, value):
        return validate_username(value)


class FollowGetViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FollowSerializer
    pagination_class = RecipesFollowsPagination

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user)


class FollowViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = FollowSerializer

    def get_queryset(self):
        return self.request.user.follower.all()

    def perform_create(self, request):
        author_id = self.kwargs.get('author_id')
        author = get_object_or_404(User, id=author_id)
        Follow.objects.create(user=self.request.user, author=author)
        serializer = FollowSerializer(
            get_object_or_404(Follow, user=request.user,
                              author=author),
            many=False
        )
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)

    def delete(self, request):
        author_id = self.kwargs.get('author_id')
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

    def get_queryset(self):
        return Favourites.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        favourite_recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        user = self.request.user
        serializer = FavouritesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=user, favourite_recipe=favourite_recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete(self, request, *args, **kwargs):
        favourite_recipe = get_object_or_404(Recipe, id=self.kwargs.get('pk'))
        Favourites.objects.get(favourite_recipe=favourite_recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ShoppingCartViewSet(
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet
):
    permission_classes = [IsAuthenticated]
    queryset = ShoppingCart.objects.all()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['recipe_id'] = self.kwargs.get('recipe_id')
        return context

    def create(self, request,  *args, **kwargs):
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
    permission_classes = [IsAuthenticated]

    def get_shopping_list(self, response):
        shopping_cart = ShoppingCart.objects.filter(user=self.request.user)
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
