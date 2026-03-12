from rest_framework.routers import DefaultRouter
from.views import EventViewset

routers = DefaultRouter()
routers.register(r"", EventViewset, basename="event")

urlpatterns = routers.urls