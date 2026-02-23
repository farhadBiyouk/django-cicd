from rest_framework import serializers

from core.news.models import Event


class EventReportCreateSerializer(serializers.Serializer):
    event_id = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=2000)

    def validate_event_id(self, event_id):
        if not Event.objects.filter(id=event_id).exists():
            raise serializers.ValidationError("event with this id does not exist")
        return event_id

    def validate_reason(self, reason):
        cleaned = reason.strip()
        if not cleaned:
            raise serializers.ValidationError("reason cannot be empty")
        return cleaned


class EventReportQuerySerializer(serializers.Serializer):
    page = serializers.IntegerField(required=False, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)
    event_id = serializers.IntegerField(required=False, min_value=1)


class EventReportSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    event_id = serializers.IntegerField(source="event", read_only=True)
    reason = serializers.CharField(read_only=True)
    reported_by_id = serializers.IntegerField(source="reported_by", read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
