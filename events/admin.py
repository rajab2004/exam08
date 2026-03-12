from django.contrib import admin
from .models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "event_type",
        "start_time",
        "end_time",
        "capacity",
        "created_by"
    )
    list_filter = ("event_type",)
    search_fields = ("title",)
