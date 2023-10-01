from django.contrib import admin

from .models import User, Tag, Recipe, Ingredient


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    pass

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    pass

@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    pass
