from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from foodgram import constants, fields
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag

User = get_user_model()


def ingredients_create(ingredients_data, recipe):
    recipe_ingredients = []
    for ingredient_data in ingredients_data:
        ingredient = Ingredient.objects.get(
            id=ingredient_data['ingredient']['id']
        )
        recipe_ingredients.append(
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient,
                amount=ingredient_data['amount']
            )
        )
    RecipeIngredient.objects.bulk_create(recipe_ingredients)


class UserStartSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    first_name = serializers.CharField(
        required=True,
        max_length=constants.MAX_LENGTH_USER
    )
    last_name = serializers.CharField(
        required=True,
        max_length=constants.MAX_LENGTH_USER
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'id']


class UserCreateSerializer(UserStartSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = list(UserStartSerializer.Meta.fields) + ['password']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserReadSerializer(UserStartSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = list(UserStartSerializer.Meta.fields) + [
            'avatar', 'is_subscribed'
        ]

    def get_is_subscribed(self, obj):
        user = self.context['request'].user
        if not user.is_authenticated:
            return False
        return user.subscriptions.filter(id=obj.id).exists()


class AvatarSerializer(serializers.ModelSerializer):
    avatar = fields.Base64ImageField(required=True)

    class Meta:
        model = User
        fields = ['avatar']


class RecipeUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time']


class SubscriptionSerializer(serializers.Serializer):
    target_user_id = serializers.IntegerField()

    def validate_target_user_id(self, value):
        user = self.context['request'].user
        target_user = get_object_or_404(User, id=value)
        if user == target_user:
            raise serializers.ValidationError(
                'Нельзя подписаться на самого себя'
            )
        if user.subscriptions.filter(id=target_user.id).exists():
            raise serializers.ValidationError('Вы уже подписаны')
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        target_user = get_object_or_404(
            User,
            id=validated_data['target_user_id']
        )
        user.subscriptions.add(target_user)
        return target_user


class SubscribeUserSerializer(UserReadSerializer):
    recipes_count = serializers.SerializerMethodField()
    recipes = RecipeUserSerializer(many=True)

    class Meta:
        model = User
        fields = list(UserReadSerializer.Meta.fields) + [
            'recipes', 'recipes_count'
        ]

    def get_recipes_count(self, obj):
        return obj.recipes.count()


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
    amount = serializers.IntegerField(
        min_value=constants.MIN_VALUE,
        max_value=constants.MAX_VALUE
    )

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
    image = fields.Base64ImageField(required=True)
    cooking_time = serializers.IntegerField(
        min_value=constants.MIN_VALUE,
        max_value=constants.MAX_VALUE
    )

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
        ingredients_create(ingredients_data, recipe)
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
        ingredients_create(ingredients_data, instance)
        return instance

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Ингредиенты обязательны.')
        ingredient_ids = set()
        for ingredient_data in value:
            ingredient_id = ingredient_data['ingredient']['id']
            if not Ingredient.objects.filter(id=ingredient_id).exists():
                raise serializers.ValidationError(
                    f'Ингредиент с id {ingredient_id} не существует.'
                )
            if ingredient_id in ingredient_ids:
                raise serializers.ValidationError(
                    f'Ингредиент с id {ingredient_id} повторяется в списке.'
                )
            ingredient_ids.add(ingredient_id)
        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError('Ингредиенты обязательны.')
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
