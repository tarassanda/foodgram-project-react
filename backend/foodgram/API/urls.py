from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (TagViewSet, GetUserToken, IngredientViewSet,
                    UserRegistrationView, UserViewSet, RecipeViewSet)

router_v1 = DefaultRouter()
router_v1.register('tags', TagViewSet, basename='tags')
router_v1.register('ingredients', IngredientViewSet, basename='Ingredients')
router_v1.register('users', UserViewSet, basename='users')
router_v1.register('recipes', RecipeViewSet, basename='tags')


auth_urls = [
    path('signup/', UserRegistrationView.as_view(), name='signup'),
    path('token/login/', GetUserToken.as_view(), name='token'),

]

urlpatterns = [
    path("", include(router_v1.urls)),
    path("auth/", include(auth_urls)),
]
