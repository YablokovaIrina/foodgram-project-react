from django.shortcuts import get_object_or_404
from rest_framework import serializers
from drf_extra_fields.fields import Base64ImageField
from recipes.models import (Favourites, Tag, TagRecipe, Recipe,
                            Ingredient, IngredientRecipe, ShoppingCart)
from users.models import User, Follow


class UserFoodCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password')

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
        return (self.context['request'].user.is_authenticated
                and Follow.objects.filter(
                    user=self.context['request'].user,
                    author=obj
        ).exists())


class RecipeFollowSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'cooking_time', 'image',)


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
        return Follow.objects.filter(
            user=self.context['request'].user,
            author=obj.author).exists()

    def validate(self, data):
        author = self.context.get('author')
        user = self.context.get('request').user
        if Follow.objects.filter(
                author=author,
                user=user).exists():
            raise serializers.ValidationError(
                detail='Вы уже подписаны на этого автора!',
            )
        if user == author:
            raise serializers.ValidationError(
                detail='Невозможно подписаться на себя!',
            )
        return data

    def get_recipes(self, obj):
        try:
            recipe_limit = int(
                self.context.get('request').query_params['recipes_limit']
            )
            queryset = Recipe.objects.filter(author=obj.author)[:recipe_limit]
        except Exception:
            queryset = Recipe.objects.filter(author=obj.author)
        serializer = FollowSerializer(queryset, read_only=True, many=True)

        return serializer.data

    def get_recipes_count(self, obj):
        return obj.author.recipes.count()


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
        fields = ('id', 'tags', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart',
                  'name', 'image', 'text', 'cooking_time',)

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        return Favourites.objects.filter(
            user=user, favourite_recipe=obj
        ).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        return ShoppingCart.objects.filter(
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
        exclude = ('pub_date',)

    def create(self, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)

        for tag in tags:
            TagRecipe.objects.create(
                tag=tag,
                recipe=recipe
            )

        for ingredient in ingredients:
            IngredientRecipe.objects.create(
                ingredient=get_object_or_404(
                    Ingredient,
                    id=ingredient['id']
                ),
                amount=ingredient['amount'],
                recipe=recipe
            )
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

        TagRecipe.objects.filter(recipe=instance).delete()
        for tag in tags:
            TagRecipe.objects.create(
                tag=get_object_or_404(
                    Tag,
                    id=tag.id),
                recipe=instance
            )

        IngredientRecipe.objects.filter(recipe=instance).delete()
        for ingredient in ingredients:
            IngredientRecipe.objects.filter(recipe=instance).create(
                ingredient=get_object_or_404(
                    Ingredient,
                    id=ingredient['id']
                ),
                amount=ingredient['amount'],
                recipe=instance
            )
        return instance


class FavouritesSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(
        source='favourite_recipe.name',
        read_only=True
    )
    image = serializers.ImageField(
        source='favourite_recipe.image',
        read_only=True
    )
    coocking_time = serializers.IntegerField(
        source='favourite_recipe.cooking_time',
        read_only=True
    )
    id = serializers.PrimaryKeyRelatedField(
        source='favourite_recipe.id',
        read_only=True
    )

    class Meta:
        model = Favourites
        fields = ('id', 'name', 'image', 'coocking_time',)

    def validate(self, data):
        user = User.objects.get(id=self.context['request'].user.id)
        favourite_recipe = Recipe.objects.get(id=self.context['recipe_id'])
        if Favourites.objects.filter(
                user=user,
                favourite_recipe=favourite_recipe
        ).exists():
            raise serializers.ValidationError(
                'Рецепт уже в избранном!'
            )
        return data


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

    def validate(self, data):
        user = User.objects.get(id=self.context['request'].user.id)
        recipe = Recipe.objects.get(id=self.context['recipe_id'])
        if ShoppingCart.objects.filter(
                user=user,
                recipe=recipe
        ).exists():
            raise serializers.ValidationError(
                'Ингредиент уже в списке покупок!'
            )
        return data
