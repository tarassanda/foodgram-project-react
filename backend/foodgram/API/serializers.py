import base64

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from foodgram_backend.models import (FavoriteRecipe, Follow, Ingredient,
                                     IngredientAmount, Recipe, ShoppingCart,
                                     Tag, User)


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class UserCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['email', 'username', 'first_name',
                  'last_name', 'password']

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return UserCreateResponseSerializer(instance, context=context).data


class UserCreateResponseSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name',]


class UserGetSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name',
                  'last_name', 'is_subscribed']

    def get_is_subscribed(self, obj):
        try:
            user = self.context.get('request').user
        except AttributeError:
            user = obj
        if user.is_anonymous:
            return False
        return Follow.objects.filter(user=user, following=obj).exists()


class FollowSerializer(UserGetSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta((UserGetSerializer.Meta)):
        fields = UserGetSerializer.Meta.fields + [
            'recipes', 'recipes_count']

    def get_recipes(self, obj):
        recipes_limit = self.context.get('recipes_limit')
        recipes = Recipe.objects.filter(author=obj)
        if recipes_limit:
            recipes = recipes[:int(recipes_limit)]
        serializer = RecipeFollowSerializer(recipes, many=True, read_only=True)
        return serializer.data

    def get_recipes_count(self, obj):
        return Recipe.objects.filter(author=obj).count()


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)


class CustomTokenSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['email', 'password']


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = ['id', 'name', 'color', 'slug']


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ['id', 'name', 'measurement_unit']


class IngredientAmountSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()
    amount = serializers.IntegerField()

    class Meta:
        model = Ingredient
        fields = ['id', 'amount']


class IngredientRecipeSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit')

    class Meta:
        model = IngredientAmount
        fields = ['id', 'name', 'measurement_unit', 'amount']


class RecipePostSerializer(serializers.ModelSerializer):
    ingredients = IngredientAmountSerializer(many=True, required=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(),
                                              many=True,
                                              required=True)
    image = Base64ImageField(required=True)

    class Meta:
        model = Recipe
        fields = ['ingredients', 'tags', 'image',
                  'name', 'text', 'cooking_time']
        read_only_fields = ['author']

    def validate_ingredients(self, value):
        ingredients = value
        if not ingredients:
            raise ValidationError({
                'ingredients': 'Ингредиенты отсутствуют!'
            })
        ingredients_list = []
        for ingredient in ingredients:
            if not Ingredient.objects.filter(id=ingredient['id']).exists():
                raise ValidationError({
                    'ingredients': 'В списке несуществующие ингредиенты!'})
            ingredient = get_object_or_404(Ingredient,
                                           id=ingredient['id'])
            if ingredient in ingredients_list:
                raise ValidationError({
                    'ingredients': 'В списке одинаковые ингредиенты!'
                })
            if int(ingredient['amount']) <= 0:
                raise ValidationError({
                    'amount': 'Количество должно быть больше 0!'
                })
            ingredients_list.append(ingredient)
        return value

    def validate_tags(self, value):
        tags = value
        if not tags:
            raise ValidationError({'tags': 'Нужно выбрать хотя бы один тег!'})
        tags_list = []
        for tag in tags:
            if tag in tags_list:
                raise ValidationError({'tags':
                                       'Теги должны быть уникальными!'})
            tags_list.append(tag)
        return value

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe_to_save = super().create(validated_data)
        recipe_to_save.tags.set(tags)
        for ingredient_to_save in ingredients:
            IngredientAmount(
                ingredient_id=ingredient_to_save.get('id'),
                amount=ingredient_to_save.get('amount'),
                recipe=recipe_to_save,).save()
        return recipe_to_save

    def update(self, recipe, validated_data):
        if 'ingredients' in validated_data:
            ingredients = validated_data.pop('ingredients')
            recipe.ingredients.clear()
            for ingredient_to_save in ingredients:
                IngredientAmount(
                    ingredient_id=ingredient_to_save.get('id'),
                    amount=ingredient_to_save.get('amount'),
                    recipe=recipe,).save()
        else:
            raise ValidationError({'ingredients': 'Нет поля ингредиентов!'})
        if 'tags' in validated_data:
            recipe.tags.set(validated_data.pop('tags'))
        else:
            raise ValidationError({'tags': 'Нет поля тегов!'})
        return super().update(
            recipe, validated_data)

    def to_representation(self, instance):
        request = self.context.get('request')
        context = {'request': request}
        return RecipeSerializer(instance, context=context).data


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    image = Base64ImageField()
    author = UserGetSerializer(read_only=True)
    ingredients = IngredientRecipeSerializer(many=True,
                                             source='ingredientamount_set')
    is_favorited = serializers.SerializerMethodField(read_only=True)
    is_in_shopping_cart = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ['id', 'tags', 'image', 'author', 'ingredients',
                  'is_favorited', 'is_in_shopping_cart', 'name',
                  'image', 'text', 'cooking_time']

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return FavoriteRecipe.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        if user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=user, recipe=obj).exists()


class RecipeFollowSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ['id', 'name', 'image', 'cooking_time',]
