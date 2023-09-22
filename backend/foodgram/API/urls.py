from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import TagViewSet

router_v1 = DefaultRouter()
router_v1.register('tags', TagViewSet, basename='categories')
router_v1.register('ingridients', TagViewSet, basename='categories')

urlpatterns = [
    path("", include(router_v1.urls))
]