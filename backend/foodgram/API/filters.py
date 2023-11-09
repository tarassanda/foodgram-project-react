import django_filters
from django_filters.rest_framework import FilterSet, filters
from foodgram_backend.models import Ingredient, Recipe, Tag


class IngredientFilter(FilterSet):
    name = django_filters.CharFilter(lookup_expr='istartswith')

    class Meta:
        model = Ingredient
        fields = ['name',]


class RecipeFilter(FilterSet):

    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='tags__slug',
        to_field_name='slug',
        queryset=Tag.objects.all(),
    )
    is_favorited = filters.BooleanFilter(field_name='is_favorited',
                                         method='favorited',)
    is_in_shopping_cart = filters.BooleanFilter(
        field_name='is_in_shopping_cart', method='shopping_cart')

    def favorited(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset
        if (value == 1) and name == 'is_favorited':
            return queryset.filter(favorites__user=user)
        return queryset

    def shopping_cart(self, queryset, name, value):
        user = self.request.user
        if user.is_anonymous:
            return queryset
        if (value == 1) and name == 'is_in_shopping_cart':
            return queryset.filter(shopping_cart__user=user)
        return queryset

    class Meta:
        model = Recipe
        fields = ['tags', 'author', 'is_favorited', 'is_in_shopping_cart']
