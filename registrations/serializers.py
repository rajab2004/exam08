from rest_framework import serializers
from .models import Registration
from events.models import Event


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Registration
        fields = ("id", "user", "event", "status", "created_at")
        read_only_fields = ("user", "status", "created_at")

    def validate(self, data):
        request = self.context["request"]
        user = request.user
        event = data["event"]

        
        if Registration.objects.filter(user=user, event=event).exists():
            raise serializers.ValidationError("Siz bu eventga allaqachon ro‘yxatdan o‘tgansiz")


        if event.capacity == 0:
            raise serializers.ValidationError("Bu eventga ro‘yxatdan o‘tish yopiq")

        
        active_count = Registration.objects.filter(
            event=event, status="registered"
        ).count()

        if active_count >= event.capacity:
            raise serializers.ValidationError("Bu eventda bo‘sh joy qolmagan")

        return data
