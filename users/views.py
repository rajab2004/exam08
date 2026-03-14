from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema  

from .models import User
from .serializers import (
    TelegramLoginSerializer, MeSerializer, MeUpdateSerializer, UpgradeToSellerSerializer
)
from marketplace.models import SellerProfile


@extend_schema(
    request=TelegramLoginSerializer,                
    responses={200: MeSerializer}                   
)
class TelegramLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ser = TelegramLoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        telegram_id = data["telegram_id"]
        username = data.get("username") or None

        user, created = User.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                "username": username or f"tg_{telegram_id}",
                "first_name": data.get("first_name", ""),
                "last_name": data.get("last_name", ""),
                "role": "customer",
            },
        )

        if username and user.username != username:
            if (user.username is None) or user.username.startswith("tg_"):
                try:
                    user.username = username
                    user.save(update_fields=["username"])
                except Exception:
                    pass

        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": MeSerializer(user).data
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "refresh required"}, status=400)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response({"detail": "invalid token"}, status=400)
        return Response({"message": "logged out"}, status=200)


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method in ("PATCH", "PUT"):
            return MeUpdateSerializer
        return MeSerializer

    def get_object(self):
        return self.request.user


class UpgradeToSellerView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role == "seller":
            return Response({"detail": "Already seller"}, status=400)

        if SellerProfile.objects.filter(user=request.user).exists():
            return Response({"detail": "SellerProfile already exists"}, status=400)

        ser = UpgradeToSellerSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data

        profile = SellerProfile.objects.create(
            user=request.user,
            shop_name=data["shop_name"],
            shop_description=data.get("shop_description", ""),
            region=data["region"],
            district=data["district"],
            address=data.get("address", ""),
        )
        request.user.role = "seller"
        request.user.save(update_fields=["role"])

        return Response({
            "message": "Upgraded to seller",
            "seller_profile_id": profile.id
        }, status=201)