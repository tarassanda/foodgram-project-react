from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (IngredientViewSet, RecipeViewSet, TagViewSet,
                    TokenLoginViewSet, TokenLogoutViewSet, UserViewSet)

router_v1 = DefaultRouter()
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='Ingredients')
router_v1.register('users', UserViewSet, basename='users')
router_v1.register('recipes', RecipeViewSet, basename='tags')


auth_urls = [
    path('token/login/', TokenLoginViewSet.as_view(), name='login'),
    path('token/logout/', TokenLogoutViewSet.as_view(), name='logout'),
]

urlpatterns = [
    path("", include(router_v1.urls)),
    path("auth/", include(auth_urls)),
]
