from datetime import datetime

from django.db.models import Sum
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate
from django.db.models import Avg
from django.http import HttpResponse, FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from urllib.parse import quote
from rest_framework import mixins, permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.permissions import IsAuthenticated

from foodgram_backend.models import (User, Tag, Recipe, Ingredient,
                                     Follow, FavoriteRecipe, IngredientAmount,
                                     ShoppingCart)
from .serializers import (TagSerializer, RecipePostSerializer,
                          UserGetSerializer, UserCreateSerializer,
                          IngredientSerializer, SetPasswordSerializer,
                          RecipeSerializer, FollowSerializer,
                          RecipeFollowSerializer)
from .filters import IngredientFilter, RecipeFilter
from .paginators import PageLimitPagination


class UserViewSet(mixins.CreateModelMixin,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()
    pagination_class = PageLimitPagination

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserGetSerializer
        return UserCreateSerializer

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[IsAuthenticated],
        url_path='me')
    def get_me_data(self, request):
        serializer = UserGetSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['POST'],
        detail=False,
        url_path='set_password',
        permission_classes=[IsAuthenticated],
        serializer_class=SetPasswordSerializer)
    def set_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.request.user
        current_password = serializer.validated_data.get('current_password')
        new_password = serializer.validated_data.get('new_password')

        if current_password != user.password:
            return Response({'message': f'{current_password} and {user.password}'},
                            status=status.HTTP_400_BAD_REQUEST)

        user.password = new_password
        user.save(update_fields=['password'])

        return Response({'message': 'Password successfully changed.'},
                        status=status.HTTP_200_OK)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        user = self.request.user
        author = get_object_or_404(User, id=pk)

        if request.method == 'POST':
            recipes_limit = request.query_params.get('recipes_limit')
            follow_pair = Follow.objects.filter(user=user, following=author)
            serializer = FollowSerializer(
                author, context={'request': request,
                                 'recipes_limit': recipes_limit})
            if user != author and not follow_pair.exists():
                Follow.objects.create(user=user, following=author)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)
            return Response(
                {'message': 'Unable to subscribe to the user.'},
                status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            if Follow.objects.filter(user=user,
                                     following=author).exists():
                follow_instance = Follow.objects.get(user=user,
                                                     following=author)
                follow_instance.delete()
                return Response({'message':
                                 'Successfully unsubscribed from the user.'})
            return Response({'message':
                             'Not subscribed to the user.'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(
        methods=['GET',],
        detail=False,
        permission_classes=[IsAuthenticated],)
    def subscriptions(self, request):
        queryset = User.objects.filter(follow_author__user=request.user)
        recipes_limit = request.query_params.get('recipes_limit')
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages, many=True, context={'request': request,
                                       'recipes_limit': recipes_limit})
        return self.get_paginated_response(serializer.data)


class TokenLoginViewSet(APIView):

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email and not password:
            return Response({'error': 'Email or password were not provided'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email, password=password)
        except User.DoesNotExist:
            user = None
        except User.MultipleObjectsReturned:
            user = None

        if user is None:
            return Response({'error': 'Invalid access data'},
                            status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({'auth_token': access_token},
                        status=status.HTTP_200_OK)


class TokenLogoutViewSet(APIView):

    def post(self, request):
        user = request.user

        try:
            token = RefreshToken.for_user(user)
            token.blacklist()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response({'error': 'Invalid token.'},
                            status=status.HTTP_401_UNAUTHORIZED)


class TagViewSet(mixins.ListModelMixin,
                 mixins.RetrieveModelMixin,
                 viewsets.GenericViewSet):
    """ViewSet для работы с тегами."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    """ViewSet для работы с ингридиентами."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с рецептами."""
    queryset = Recipe.objects.all()
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = PageLimitPagination
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return RecipePostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=['POST', 'DELETE'],
        detail=True,
        queryset=FavoriteRecipe.objects.all(),
        permission_classes=[permissions.IsAuthenticated])
    def favorite(self, request, pk=None):
        user = self.request.user
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'POST':
            serializer = RecipeFollowSerializer(recipe)
            if not FavoriteRecipe.objects.filter(user=user,
                                                 recipe=recipe).exists():
                FavoriteRecipe.objects.create(user=user, recipe=recipe)
                return Response(
                    serializer.data, status=status.HTTP_201_CREATED)
            return Response(
                {'message': 'Unable to add recipe to favorite.'},
                status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            if FavoriteRecipe.objects.filter(user=user,
                                             recipe=recipe).exists():
                follow_instance = FavoriteRecipe.objects.get(user=user,
                                                             recipe=recipe)
                follow_instance.delete()
                return Response({'message':
                                 'Successfully deleted recipe from favorite.'})
            return Response({'message':
                             'Recipe not in favorite.'},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=['POST', 'DELETE'],
        queryset=ShoppingCart.objects.all(),
        permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        user = request.user
        if request.method == 'POST':
            return self.add_to(ShoppingCart, user, pk)
        else:
            return self.delete_from(ShoppingCart, user, pk)

    def add_to(self, ShoppingCart, user, pk):
        if ShoppingCart.objects.filter(user=user, recipe__id=pk).exists():
            return Response({'message': 'Recipe already added!'},
                            status=status.HTTP_400_BAD_REQUEST)
        recipe = get_object_or_404(Recipe, id=pk)
        ShoppingCart.objects.create(user=user, recipe=recipe)
        serializer = RecipeFollowSerializer(recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def delete_from(self, ShoppingCart, user, pk):
        if ShoppingCart.objects.filter(user=user, recipe__id=pk).exists():
            ShoppingCart.objects.filter(user=user, recipe__id=pk).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({'message': 'Recipe already deleted!'},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        if not user.shopping_cart.exists():
            return Response(status=status.HTTP_400_BAD_REQUEST)

        ingredients = IngredientAmount.objects.filter(
            recipe__shopping_cart__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount'))

        today = datetime.today()
        shopping_list = (
            f'Список покупок для: {user.get_full_name()}\n\n'
            f'Дата: {today:%Y-%m-%d}\n\n'
        )
        shopping_list += '\n'.join([
            f'- {ingredient["ingredient__name"]} '
            f'({ingredient["ingredient__measurement_unit"]})'
            f' - {ingredient["amount"]}'
            for ingredient in ingredients
        ])
        shopping_list += f'\n\nFoodgram ({today:%Y})'

        filename = f'{user.username}_shopping_list.txt'
        quoted_filename = quote(filename)
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{quoted_filename}"'

        return response
