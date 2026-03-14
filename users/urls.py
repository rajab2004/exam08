from django.urls import path
from .views import MeView, UpgradeToSellerView

urlpatterns = [
    path("users/me/", MeView.as_view()),
    path("users/me/upgrade-to-seller/", UpgradeToSellerView.as_view()),
]