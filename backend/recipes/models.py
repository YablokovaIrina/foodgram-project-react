from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from foodgram.settings import (MAX_AMOUNT, MAX_COOKING_TIME, MAX_LENGHT,
                               MAX_LENGHT_COLOR, MIN_AMOUNT, MIN_COOKING_TIME,)
from users.models import User


class Tag(models.Model):
    name = models.CharField(
        max_length=MAX_LENGHT,
        unique=True,
        verbose_name='Название'
    )
    color = models.CharField(
        max_length=MAX_LENGHT_COLOR,
        null=True,
        verbose_name='Цвет в HEX'
    )
    slug = models.SlugField(
        max_length=MAX_LENGHT,
        unique=True,
        null=True,
        verbose_name='Идентификатор'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def str(self):
        return (
            f'Название: {self.name}, '
            f'Цвет: {self.color}, '
            f'Индентификатор: {self.slug}'
        )


class Ingredient(models.Model):
    name = models.CharField(
        max_length=MAX_LENGHT,
        verbose_name='Название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=MAX_LENGHT,
        verbose_name='Единица измерения'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def str(self):
        return (
            f'Название ингредиента : {self.name}, '
            f'Единица измерения: {self.measurement_unit}'
        )


class Recipe(models.Model):
    name = models.CharField(
        max_length=MAX_LENGHT,
        verbose_name='Название рецепта'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        related_name='recipes'
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    image = models.ImageField(
        verbose_name='Изображение',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(MIN_COOKING_TIME, message='Не менее 1 минуты!'),
            MaxValueValidator(MAX_COOKING_TIME)
        ],
        verbose_name='Время приготовление'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientRecipe',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        through='TagRecipe',
        verbose_name='Теги'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Дата публикации'
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def str(self):
        return self.name


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Ингредиент',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(MIN_AMOUNT),
                    MaxValueValidator(MAX_AMOUNT)]
    )

    class Meta:
        ordering = ('ingredient',)
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'

    def str(self):
        return f'{self.ingredient.name} {self.amount}'


class TagRecipe(models.Model):
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ('tag',)
        verbose_name = 'Тег в рецепте'

    def str(self):
        return f'{self.tag.slug} {self.recipe.name}'


class Favourites(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта',
        related_name='favorite_recipe',
    )
    favorite_recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe',
        verbose_name='Избранный рецепт'
    )

    class Meta:
        ordering = ('favorite_recipe',)
        constraints = [
            models.UniqueConstraint(
                fields=('favorite_recipe', 'user'),
                name='unique_favorite_recipe',
            ),
        ]
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранные'

    def str(self):
        return (
            f'{self.user.username} добавил'
            f'{self.favourite_recipe.name} в избранное'
        )


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_cart',
        verbose_name='Рецепт'
    )

    class Meta:
        ordering = ('recipe',)
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart_recipe',
            ),
        )
        verbose_name = 'Список покупок'

    def str(self):
        return f'{self.recipe.name} в списке покупок {self.user.username}'
