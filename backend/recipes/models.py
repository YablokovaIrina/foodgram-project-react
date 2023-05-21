from django.core.validators import MinValueValidator
from django.db import models

from foodgram.settings import MAX_LENGHT, MAX_LENGHT_COLOR
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
    )
    text = models.TextField(
        verbose_name='Описание'
    )
    image = models.ImageField(
        verbose_name='Изображение',
    )
    cooking_time = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1, message='Не менее 1 минуты!')
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
        ordering = ['-id']
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def str(self):
        return self.name


class IngredientRecipe(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент',
        related_name='recipe_ingredients',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        verbose_name='Рецепт',
    )
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)]
    )

    class Meta:
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

    def str(self):
        return f'{self.tag.slug} {self.recipe.name}'


class Favourites(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор рецепта'
    )
    favourite_recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipe',
        verbose_name='Избранный рецепт'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=('favourite_recipe', 'user'),
                name='unique_favourite_recipe',
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
        constraints = (
            models.UniqueConstraint(
                fields=('user', 'recipe'),
                name='unique_shopping_cart_recipe',
            ),
        )
        verbose_name = 'Список покупок'

    def str(self):
        return f'{self.recipe.name} в списке покупок {self.user.username}'
