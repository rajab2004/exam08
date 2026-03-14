from rest_framework import serializers
from .models import User
from marketplace.models import SellerProfile

class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "telegram_id", "username", "first_name", "last_name", "phone_number", "role", "avatar")

class MeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone_number", "avatar")

class TelegramLoginSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField()
    username = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    photo_url = serializers.URLField(required=False, allow_blank=True)

class UpgradeToSellerSerializer(serializers.Serializer):
    shop_name = serializers.CharField(max_length=120)
    shop_description = serializers.CharField(required=False, allow_blank=True)
    region = serializers.CharField(max_length=120)
    district = serializers.CharField(max_length=120)
    address = serializers.CharField(required=False, allow_blank=True)