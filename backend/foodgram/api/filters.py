import django_filters
from django_filters.rest_framework import FilterSet, filters
from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    name = django_filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(FilterSet):

    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(method='favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='shopping_cart')

    def favorited(self, queryset, name, value):
        if self.request.user.is_anonymous:
            return queryset
        if value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def shopping_cart(self, queryset, name, value):
        if self.request.user.is_anonymous:
            return queryset
        if value:
            return queryset.filter(shopping_cart__user=self.request.user)
        return queryset

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']
