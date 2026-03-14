from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet, ProductViewSet,
    FavoriteViewSet, OrderViewSet, ReviewViewSet,
    SellerViewSet,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet, basename="categories")
router.register(r"products", ProductViewSet, basename="products")
router.register(r"favorites", FavoriteViewSet, basename="favorites")
router.register(r"orders", OrderViewSet, basename="orders")
router.register(r"reviews", ReviewViewSet, basename="reviews")
router.register(r"sellers", SellerViewSet, basename="sellers")

urlpatterns = [
    path("", include(router.urls)),
]