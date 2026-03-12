from django.shortcuts import render
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response

from .models import Registration
from .serializers import RegistrationSerializer
from events.models import Event


class RegisterForEventView(generics.CreateAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CancelRegistrationView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        event_id = kwargs.get("event_id")

        registration = get_object_or_404(
            Registration,
            user=request.user,
            event_id=event_id,
            status="registered",
        )

        registration.status = "cancelled"
        registration.save()

        return Response(
            {"detail": "Registration bekor qilindi"},
            status=status.HTTP_200_OK,
        )
