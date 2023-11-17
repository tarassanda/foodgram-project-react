from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (FavoriteRecipe, Follow, Ingredient, IngredientAmount,
                     Recipe, ShoppingCart, Tag, User)


class IngredientAmountInline(admin.TabularInline):
    model = IngredientAmount
    extra = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    inlines = (IngredientAmountInline,)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    pass


@admin.register(User)
class UserAdmin(UserAdmin):
    pass


@admin.register(IngredientAmount)
class IngredientAmountAdmin(admin.ModelAdmin):
    pass


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    pass


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    pass


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    pass
