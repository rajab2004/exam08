from django.urls import path
from .views import RegisterForEventView, CancelRegistrationView

urlpatterns = [
    path("register/", RegisterForEventView.as_view(), name="register-for-event"),
    path("cancel/<int:event_id>/", CancelRegistrationView.as_view(), name="cancel-registration"),
]
