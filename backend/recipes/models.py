from django.contrib.auth import get_user_model
from django.db import models

from foodgram.constants import MAX_LENGTH, MAX_TEXT_LENGHT, LENGTH_SHORT_LINK

User = get_user_model()


class Tag(models.Model):
    name = models.CharField('Тэг', max_length=MAX_LENGTH)
    slug = models.SlugField()

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField('Название ингридиента', max_length=MAX_LENGTH)
    measurement_unit = models.CharField(
        'Единицы измерения', max_length=MAX_LENGTH
    )

    def __str__(self):
        return self.name


class Recipe(models.Model):
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        verbose_name='Автор', related_name='recipes'
    )
    name = models.CharField(
        max_length=MAX_LENGTH,
        verbose_name='Название рецепта'
    )
    image = models.ImageField()
    text = models.TextField(
        verbose_name='Описание',
        max_length=MAX_TEXT_LENGHT
    )
    tags = models.ManyToManyField(Tag,)
    cooking_time = models.IntegerField(verbose_name='Время готовки')
    ingredients = models.ManyToManyField(
        Ingredient,
        verbose_name='Ингридиенты',
        through='RecipeIngredient',
        related_name='ingredient_recipes'
    )
    favorited = models.ManyToManyField(User, related_name='favorite')
    shopping_carted = models.ManyToManyField(User, related_name='in_cart')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] 

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredient'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='ingredient_recipe'
    )
    amount = models.IntegerField('Количество')

    class Meta:
        unique_together = ('recipe', 'ingredient')

    def __str__(self):
        return f'{self.recipe.name} - {self.ingredient.name}'


class ShortLink(models.Model):
    short_code = models.CharField(
        max_length=LENGTH_SHORT_LINK,
        unique=True,
    )
    original_recipe_id = models.IntegerField()

    def __str__(self):
        return f'{self.short_code} -> {self.original_recipe_id}'
