from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import authenticate
from django.db.models import Avg
from django.db import IntegrityError
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
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from foodgram_backend.models import (User, Tag, Recipe, Ingredient)
from .serializers import (TagSerializer, RecipeSerializer, UserSerializer,
                          IngredientSerializer, UserRegistrationSerializer,
                          CustomTokenSerializer)


FROM_WHO_EMAIL_ADDRESS = 'api_yamdb@kogorta.com'


class CreateListDestroyViewSet(mixins.CreateModelMixin,
                               mixins.ListModelMixin,
                               mixins.DestroyModelMixin,
                               viewsets.GenericViewSet):
    filter_backends = (SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('username',)
    lookup_field = 'username'
    http_method_names = ['get', 'post', 'head', 'patch', 'delete']
    permission_classes = [permissions.AllowAny]

    @action(
        methods=['GET'],
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        url_path='me')
    def get_me_data(self, request):
        """Позволяет пользователю получить информацию о своём профиле."""
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserRegistrationView(APIView):
    """View-класс для создания пользователя."""
    permission_classes = [permissions.AllowAny]

    def send_confirmation_code(self, user, username, user_email):
        """Генерирует confirmation_code и отсылает пользователю."""
        code = default_token_generator.make_token(user)
        send_mail(
            f'Confirmation code for {username}',
            f'Ваш код подтверждения: {code}',
            FROM_WHO_EMAIL_ADDRESS,
            [user_email]
        )

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        user_email = serializer.validated_data['email']

        try:
            user, _ = User.objects.get_or_create(
                username=username,
                email=user_email
            )

        except IntegrityError:
            raise ValidationError(
                'Пользователь с таким username или \
email уже существует.')

        self.send_confirmation_code(user, username, user_email)
        return Response(serializer.validated_data)


class GetUserToken(APIView):
    """View-класс для получения JWT-access-токена."""
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
    serializer_class = RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
