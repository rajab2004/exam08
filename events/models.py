from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class Event(models.Model):
    EVENT_TYPE_CHOICES = (
        ("ONLINE", "Online"),
        ("OFFLINE", "Offline"),
    )

    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(
        max_length=10,
        choices=EVENT_TYPE_CHOICES
    )
    location = models.CharField(max_length=255, null=True, blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    capacity = models.IntegerField()

    created_by = models.ForeignKey(       
        settings.AUTH_USER_MODEL,           
        on_delete=models.CASCADE,
        related_name="events"
    )

    created_at = models.DateTimeField(auto_now_add=True)  

    def clean(self):
        if self.capacity < 0:
            raise ValidationError("Capacity manfiy bo‘lishi mumkin emas")

        if self.end_time < self.start_time:
            raise ValidationError(
                "end_time start_time dan kichik bo‘lishi mumkin emas"
            )

        if self.event_type == "OFFLINE" and not self.location:
            raise ValidationError(
                "Offline event uchun location kiritish shart"
            )

        if self.event_type == "ONLINE":
            self.location = None

    def __str__(self):
        return self.title
