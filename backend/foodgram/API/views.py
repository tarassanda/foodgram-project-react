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

from foodgram_backend.models import (User, Tag, Recipe, Ingredient, Follow)
from .serializers import (TagSerializer, RecipePostSerializer,
                          UserGetSerializer, UserCreateSerializer,
                          IngredientSerializer, SetPasswordSerializer,
                          RecipeSerializer, FollowSerializer)


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
        queryset=Follow.objects.all(),
        methods=['post'],
        detail=True,
        permission_classes=[permissions.IsAuthenticated]
        )
    def subscribe(self, request, pk=None):
        user_to_follow = get_object_or_404(User, id=pk)
        user = self.request.user
        if user != user_to_follow and not Follow.objects.filter(user=user, following=user_to_follow).exists():
            Follow.objects.create(user=user, following=user_to_follow)
            return Response({'message': 'Successfully subscribed to user.'})
        return Response({'message': 'Unable to subscribe to the user.'}, status=400)

    @action(
        queryset=Follow.objects.all(),
        methods=['delete'],
        detail=True,
        permission_classes=[permissions.IsAuthenticated])
    def unsubscribe(self, request, pk=None):
        user_to_unfollow = get_object_or_404(User, id=pk)
        user = self.request.user
        if Follow.objects.filter(user=user,
                                 following=user_to_unfollow).exists():
            follow_instance = Follow.objects.get(user=user,
                                                 following=user_to_unfollow)
            follow_instance.delete()
            return Response({'message':
                             'Successfully unsubscribed from the user.'})
        return Response({'message': 'Not subscribed to the user.'}, status=400)

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
