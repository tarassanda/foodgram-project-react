from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate
from django.db.models import Avg
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
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
                                     Follow, FavoriteRecipe)
from .serializers import (TagSerializer, RecipePostSerializer,
                          UserGetSerializer, UserCreateSerializer,
                          IngredientSerializer, SetPasswordSerializer,
                          RecipeSerializer, FollowSerializer,
                          RecipeFollowSerializer)
from .filters import IngredientFilter


class CreateListDestroyViewSet(mixins.CreateModelMixin,
                               mixins.ListModelMixin,
                               mixins.DestroyModelMixin,
                               viewsets.GenericViewSet):
    filter_backends = (SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class UserViewSet(mixins.CreateModelMixin,
                  mixins.ListModelMixin,
                  mixins.RetrieveModelMixin,
                  viewsets.GenericViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserGetSerializer
        return UserCreateSerializer

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        url_path='me')
    def get_me_data(self, request):
        """Позволяет пользователю получить информацию о своём профиле."""
        serializer = UserGetSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['POST'],
        detail=False,
        url_path='set_password',
        permission_classes=[permissions.IsAuthenticated],
        serializer_class=SetPasswordSerializer)
    def set_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.request.user
        current_password = serializer.validated_data.get('current_password')
        new_password = serializer.validated_data.get('new_password')

        if current_password != user.password:
            return Response({'message': 'Invalid current password.'},
                            status=400)

        user.password = new_password
        user.save(update_fields=['password'])

        return Response({'message': 'Password successfully changed.'},
                        status=200)

    @action(
        methods=['post', 'delete'],
        detail=True,
        permission_classes=[permissions.IsAuthenticated])
    def subscribe(self, request, pk=None):
        user = self.request.user
        author = get_object_or_404(User, id=pk)

        if request.method == 'POST':
            recipes_limit = request.query_params.get('recipes_limit')
            serializer = FollowSerializer(
                author, context={"request": request, "recipes_limit": recipes_limit})
            if user != author and not Follow.objects.filter(user=user, following=author).exists():
                Follow.objects.create(user=user, following=author)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({'message': 'Unable to subscribe to the user.'}, status=400)

        if request.method == 'DELETE':
            if Follow.objects.filter(user=user,
                                     following=author).exists():
                follow_instance = Follow.objects.get(user=user,
                                                     following=author)
                follow_instance.delete()
                return Response({'message':
                                 'Successfully unsubscribed from the user.'})
            return Response({'message': 'Not subscribed to the user.'}, status=400)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        user = request.user
        queryset = User.objects.filter(subscribing__user=user)
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(pages,
                                      many=True,
                                      context={'request': request})
        return self.get_paginated_response(serializer.data)


class TokenLoginViewSet(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email and not password:
            return Response({'error': 'Отсутствует пароль или email'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email, password=password)
        except User.DoesNotExist:
            user = None
        except User.MultipleObjectsReturned:
            user = None

        if user is None:
            return Response({'error': 'Неверные данные входа'},
                            status=status.HTTP_401_UNAUTHORIZED)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        return Response({'auth_token': access_token},
                        status=status.HTTP_200_OK)


class TokenLogoutViewSet(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        try:
            token = RefreshToken.for_user(user)
            token.blacklist()
            return Response({'message': 'Successfully logged out.'},
                            status=status.HTTP_204_NO_CONTENT)
        except Exception:
            return Response({'error': 'Invalid token.'},
                            status=status.HTTP_400_BAD_REQUEST)


class TagViewSet(mixins.ListModelMixin,
                 mixins.CreateModelMixin,
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

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeSerializer
        return RecipePostSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        methods=['post', 'delete'],
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
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response({'message': 'Unable to add recipe to favorite.'}, status=400)

        if request.method == 'DELETE':
            if FavoriteRecipe.objects.filter(user=user,
                                             recipe=recipe).exists():
                follow_instance = FavoriteRecipe.objects.get(user=user,
                                                             recipe=recipe)
                follow_instance.delete()
                return Response({'message':
                                 'Successfully deleted recipe from favorite.'})
            return Response({'message': 'Recipe not in favorite.'}, status=400)








# class SubscribeSerializer(CustomUserSerializer):
#     recipes_count = SerializerMethodField()
#     recipes = SerializerMethodField()

#     class Meta(CustomUserSerializer.Meta):
#         fields = CustomUserSerializer.Meta.fields + (
#             'recipes_count', 'recipes'
#         )
#         read_only_fields = ('email', 'username')

#     def validate(self, data):
#         author = self.instance
#         user = self.context.get('request').user
#         if Subscribe.objects.filter(author=author, user=user).exists():
#             raise ValidationError(
#                 detail='Вы уже подписаны на этого пользователя!',
#                 code=status.HTTP_400_BAD_REQUEST
#             )
#         if user == author:
#             raise ValidationError(
#                 detail='Вы не можете подписаться на самого себя!',
#                 code=status.HTTP_400_BAD_REQUEST
#             )
#         return data

#     def get_recipes_count(self, obj):
#         return obj.recipes.count()

#     def get_recipes(self, obj):
#         request = self.context.get('request')
#         limit = request.GET.get('recipes_limit')
#         recipes = obj.recipes.all()
#         if limit:
#             recipes = recipes[:int(limit)]
#         serializer = RecipeShortSerializer(recipes, many=True, read_only=True)
#         return serializer.data
