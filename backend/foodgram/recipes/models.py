from colorfield.fields import ColorField
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .validators import validate_username


class User(AbstractUser):

    email = models.EmailField(
        max_length=254,
        unique=True,
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=(validate_username,)
    )
    first_name = models.CharField(
        'Имя',
        max_length=150,
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=150,
    )

    class Meta:
        ordering = ('username',)

    def __str__(self):
        return self.username


class Tag(models.Model):
    """Модель для Tags"""
    name = models.CharField(max_length=200, verbose_name='Тег')
    color = ColorField(format='hexa', verbose_name='Цвет')
    slug = models.SlugField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    """Модель для Ingredients"""
    name = models.CharField(max_length=200, verbose_name='Ингредиент')
    measurement_unit = models.CharField(max_length=200)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name', 'measurement_unit'],
                                    name='unique_name_and_measurement')
        ]

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель для Recipes"""
    name = models.CharField(max_length=200, verbose_name='Название рецепта')
    text = models.TextField(
        verbose_name='Описание',
        help_text='Опишите, о чём произведение.'
    )
    ingredients = models.ManyToManyField(
        'Ingredient',
        through='IngredientAmount',
        through_fields=('recipe', 'ingredient'),
        related_name='ingredients',
        verbose_name='Ингридиенты'
    )
    tags = models.ManyToManyField(
        'Tag',
        related_name='tags',
        verbose_name='Тег',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authors',
        verbose_name='Автор'
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='recipes/',
        help_text="Загрузить изображение",
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (минут)',
        validators=[MinValueValidator(
            limit_value=1, message='Невозможно приготовить за 0 минут!'), ])

    def __str__(self):
        return self.name


class IngredientAmount(models.Model):
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        verbose_name='Ингредиент')
    amount = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(
            limit_value=1, message='Количество должно быть больше 0'),
            MaxValueValidator(
            limit_value=3000, message='Количество должно быть не больше 3000'),
        ])
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['ingredient', 'recipe'],
                                    name='unique_ingredient_in_recipe')
        ]


class FavoriteRecipe(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Подписчик'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        verbose_name='Рецепт'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_favorite_recipe')
        ]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follow_follower',
        verbose_name='Подписчик'
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follow_author',
        verbose_name='Автор'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                name='Unique_follow',
                fields=['following', 'user']
            ),
            models.CheckConstraint(
                check=~models.Q(following=models.F('user')),
                name='user_cannot_follow_themselves'
            )
        ]


class ShoppingCart(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='shopping_cart',
        verbose_name='Рецепт',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'recipe'],
                                    name='unique_shopping_cart')
        ]
