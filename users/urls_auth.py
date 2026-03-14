from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import TelegramLoginView, LogoutView

urlpatterns = [
    path("telegram-login/", TelegramLoginView.as_view()),
    path("refresh/", TokenRefreshView.as_view()),
    path("logout/", LogoutView.as_view()),
]