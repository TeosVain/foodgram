from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from foodgram import constants, fields
from recipes.models import Recipe

User = get_user_model()


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
