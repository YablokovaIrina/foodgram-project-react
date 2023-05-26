from django.shortcuts import get_object_or_404
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from recipes.models import (Favourites, Ingredient, IngredientRecipe, Recipe,
                            ShoppingCart, Tag, TagRecipe,)
from users.models import Follow, User


class UserFoodCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password')
        required_fields = (
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserFoodSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and obj.follower.filter(
                user=user,
                author=obj
            ).exists()
        )


class RecipeFollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image')


class FollowSerializer(serializers.ModelSerializer):
    email = serializers.CharField(
        read_only=True,
        source='author.email'
    )
    id = serializers.CharField(
        read_only=True,
        source='author.id'
    )
    username = serializers.CharField(
        read_only=True,
        source='author.username'
    )
    first_name = serializers.CharField(
        read_only=True,
        source='author.first_name'
    )
    last_name = serializers.CharField(
        read_only=True,
        source='author.last_name'
    )
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Follow
        fields = ('email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed', 'recipes', 'recipes_count')

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (
            user.is_authenticated
            and obj.follower.filter(
                user=user,
                author=obj
            ).exists()
        )

    def validate(self, data):
        author_id = self.context.get(
            'request').parser_context.get('kwargs').get('id')
        author = get_object_or_404(User, id=author_id)
        user = self.context.get('request').user
        if user.follower.filter(author=author).exists():
            raise serializers.ValidationError(
                detail='Вы уже подписаны на этого автора!',
            )
        if user == author:
            raise serializers.ValidationError(
                detail='Невозможно подписаться на себя!',
            )
        return data

    def get_recipes(self, obj):
        queryset = obj.recipes.all()
        limit = self.context['request'].query_params['recipes_limit']
        if limit:
            try:
                limit = int(limit)
                queryset = queryset[:limit]
            except ValueError:
                pass
        serializer = RecipeFollowSerializer(queryset, many=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient.id', read_only=True)
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = UserFoodSerializer(read_only=True)
    tags = TagSerializer(
        many=True
    )
    ingredients = IngredientRecipeSerializer(
        many=True,
        read_only=True,
        source='recipe_ingredients'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return obj.favorite_recipe.filter(
            user=user,
            favorite_recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return obj.in_shopping_cart.filter(
            user=user,
            recipe=obj
        ).exists()


class IngredientRecipeWriteSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = IngredientRecipe
        fields = ('id', 'amount')
        required_fields = ('id', 'amount')


class RecipeWriteSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    tags = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all())
    )
    ingredients = IngredientRecipeWriteSerializer(many=True)
    image = Base64ImageField()
    cooking_time = serializers.IntegerField()

    class Meta:
        model = Recipe
        required_fields = (
            'ingredients',
            'tags',
            'image',
            'name',
            'text',
            'cooking_time'
        )
        exclude = ('pub_date',)

    def add_tags(self, tags, recipe):
        tags = []
        for tag in tags:
            TagRecipe(
                tag=tag,
                recipe=recipe
            )
        TagRecipe.objects.bulk_create(tags)

    def add_ingredient(self, ingredients, recipe):
        ingredients = []
        for ingredient in ingredients:
            IngredientRecipe(
                recipe=recipe,
                amount=ingredient['amount'],
                ingredient=ingredient['id']
            )
            ingredients.append(ingredient)
        IngredientRecipe.objects.bulk_create(ingredients)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        self.add_tags(tags, recipe)
        self.add_ingredient(ingredients, recipe)
        return recipe

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        instance.image = validated_data.get('image', instance.image)
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get(
            'cooking_time',
            instance.cooking_time
        )
        instance.save()
        self.add_tags(tags, instance)
        self.add_ingredient(ingredients, instance)
        return instance


class FavouritesSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(
        source='favorite_recipe.name',
        read_only=True
    )
    image = serializers.ImageField(
        source='favorite_recipe.image',
        read_only=True
    )
    coocking_time = serializers.IntegerField(
        source='favorite_recipe.cooking_time',
        read_only=True
    )
    id = serializers.PrimaryKeyRelatedField(
        source='favorite_recipe.id',
        read_only=True
    )

    class Meta:
        model = Favourites
        fields = ('id', 'name', 'image', 'coocking_time',)

    def validate(self, recipe):
        if recipe.favorite_recipe.exists():
            raise serializers.ValidationError(
                'Рецепт уже в избранном!'
            )
        return recipe


class ShoppingCartSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        source='recipe.name',
        read_only=True
    )
    image = serializers.ImageField(
        source='recipe.image',
        read_only=True
    )
    coocking_time = serializers.IntegerField(
        source='recipe.cooking_time',
        read_only=True
    )
    id = serializers.PrimaryKeyRelatedField(
        source='recipe.id',
        read_only=True
    )

    class Meta:
        model = ShoppingCart
        fields = ('id', 'name', 'image', 'coocking_time')

    def validate(self, recipe):
        if recipe.in_shopping_cart.exists():
            raise serializers.ValidationError(
                'Ингредиент уже в списке покупок!'
            )
        return recipe
