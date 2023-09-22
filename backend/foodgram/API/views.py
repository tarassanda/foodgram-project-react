from django.core.mail import send_mail
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

from foodgram_backend.models import (User, Tag, Recipe, Ingridient)
from .serializers import (TagSerializer, RecipeSerializer,
                          IngridientSerializer, UserSerializer)


FROM_WHO_EMAIL_ADDRESS = 'api_yamdb@kogorta.com'


class CreateListDestroyViewSet(mixins.CreateModelMixin,
                               mixins.ListModelMixin,
                               mixins.DestroyModelMixin,
                               viewsets.GenericViewSet):
    filter_backends = (SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class TagViewSet(CreateListDestroyViewSet):
    """ViewSet для работы с категориями."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngridientViewSet(CreateListDestroyViewSet):
    """ViewSet для работы с категориями."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
