from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Event
from .serializers import EventSerializer

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.metod in permissions.Save_Methhods:
            return True

        return request.user and request.user.is_staff
    


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().order_by('-created_at')
    serializer_class = EventSerializer
    permissions_classes = [IsAdminOrReadOnly]

    def perfom_create(self, serializer):
        serializer.save(created_by=self.request.user)    