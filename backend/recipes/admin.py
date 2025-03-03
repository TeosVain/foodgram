from django.contrib import admin

from recipes.models import Ingredient, Recipe, RecipeIngredient, ShortLink, Tag


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'author')
    search_fields = ('author', 'name')
    list_filter = ('tags__name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('name', 'measurement_unit')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(RecipeIngredient)
class RecipeIngAdmin(admin.ModelAdmin):
    pass


@admin.register(ShortLink)
class ShortLinkAdmin(admin.ModelAdmin):
    pass
