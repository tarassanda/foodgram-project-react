from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .validators import validate_username, validate_year


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
    password = models.CharField(
        'Пароль',
        max_length=150,
        blank=True
    )
    
    class Meta:
        ordering = ('username',)

    def __str__(self):
        return self.username


class Tag(models.Model):
    """Модель для Tags"""
    name = models.CharField(max_length=200, verbose_name='Тег')
    color = models.CharField(max_length=7, null=False, verbose_name='Цвет')
    slug = models.SlugField(max_length=200, null=False, unique=True)

    def __str__(self):
        return self.name


class Ingridient(models.Model):
    """Модель для Ingridients"""
    name = models.CharField(max_length=200, verbose_name='Ингридиент')
    measurement_unit = models.CharField(max_length=200, null=False)

    def __str__(self):
        return self.name


class Recipe(models.Model):
    """Модель для Recipes"""
    name = models.CharField(max_length=200, verbose_name='Название рецепта')
    text = models.TextField(
        verbose_name='Описание',
        help_text='Опишите, о чём произведение.'
    )
    ingridients = models.ManyToManyField(
        'Ingridient',
        related_name='ingridients',
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
        upload_to='foodgram_backend/',
        help_text="Загрузить изображение",
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления (минут)')
    
    def __str__(self):
        return self.name
