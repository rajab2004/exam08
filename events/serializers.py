from rest_framework import serializers
from .models import Event

class EventSerializer(serializers.ModelSerializer):
    created_at = serializers.ReadOnlyField(source='created_at.username')


    class Meta:
        model = Event
        fields = (
             "id",
            "title",
            "description",
            "event_type",
            "location",
            "start_time",
            "end_time",
            "capacity",
            "created_by",
            "created_at",
        )

    def validate(self, date):
        start_time = date.get('start_time')
        end_time = date.get('end_time')

        if start_time and end_time and end_time < start_time:
            raise serializers.ValidationError(
                {end_time: "end_time start_time dan kichik bolishi mumkun emas"}

            )
        return date


