from django.contrib.auth import get_user_model
from rest_framework import serializers

from foodgram.fields import Base64ImageField
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag
from user.serializers import UserReadSerializer

User = get_user_model()


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Ingredient


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ['id', 'name', 'measurement_unit', 'amount']


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        fields = '__all__'
        model = Tag


class RecipeSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientSerializer(
        source='recipe_ingredient', many=True, required=True
    )
    author = UserReadSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(min_value=1)

    class Meta:
        model = Recipe
        fields = [
            'id',
            'name',
            'image',
            'text',
            'cooking_time',
            'author',
            'tags',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart'
        ]

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.favorited.filter(id=user.id).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.shopping_carted.filter(id=user.id).exists()
        return False

    def create(self, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredient')
        tags_data = validated_data.pop('tags')
        user = self.context['request'].user
        recipe = Recipe.objects.create(author=user, **validated_data)
        recipe.tags.set(tags_data)
        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(
                id=ingredient_data['ingredient']['id']
            )
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data['amount']
            )
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('recipe_ingredient', None)
        if ingredients_data is None:
            raise serializers.ValidationError('Ингредиенты обязательны.')
        tags_data = validated_data.pop('tags', None)
        if tags_data is None:
            raise serializers.ValidationError('Теги обязательны.')
        instance = super().update(instance, validated_data)
        instance.tags.set(tags_data)
        instance.recipe_ingredient.all().delete()
        for ingredient_data in ingredients_data:
            ingredient = Ingredient.objects.get(
                id=ingredient_data['ingredient']['id']
            )
            RecipeIngredient.objects.create(
                recipe=instance,
                ingredient=ingredient,
                amount=ingredient_data['amount']
            )
        return instance

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Ингредиенты обязательны.")
        ingredient_ids = set()
        for ingredient_data in value:
            ingredient_id = ingredient_data['ingredient']['id']
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(
                    f'Ингредиент с id {ingredient_id} не существует.'
                )
            if ingredient_data['amount'] < 1:
                raise serializers.ValidationError(
                    f'Количество ингредиента с id {ingredient_id} меньше 1.'
                )
            if ingredient_id in ingredient_ids:
                raise serializers.ValidationError(
                    f'Ингредиент с id {ingredient_id} повторяется в списке.'
                )
            ingredient_ids.add(ingredient_id)
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError("Ингредиенты обязательны.")
        tags_included = set()
        for tag_data in value:
            if tag_data in tags_included:
                raise serializers.ValidationError(
                    f'Тэги {tag_data} повторяется в списке.'
                )
            tags_included.add(tag_data)
        return value


class RecipeWriteSerializer(RecipeSerializer):
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=True
    )


class RecipeReadSerializer(RecipeSerializer):
    tags = TagSerializer(many=True)
