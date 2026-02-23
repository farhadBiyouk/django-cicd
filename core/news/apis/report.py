from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.mixins import ApiAuthMixin
from core.news.models import Event, EventReport


class EventReportApi(ApiAuthMixin, APIView):
    class InputSerializer(serializers.Serializer):
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

    class OutputSerializer(serializers.ModelSerializer):
        event_id = serializers.IntegerField(source="event_id", read_only=True)
        reported_by = serializers.IntegerField(source="reported_by_id", read_only=True)

        class Meta:
            model = EventReport
            fields = ("id", "event_id", "reason", "reported_by", "created_at", "updated_at")

    @extend_schema(
        tags=["news"],
        summary="Submit event report",
        description="Create a report for an event using event_id and reason",
        request=InputSerializer,
        responses=OutputSerializer,
    )
    def post(self, request):
        serializer = self.InputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report = EventReport.objects.create(
            event_id=serializer.validated_data["event_id"],
            reason=serializer.validated_data["reason"],
            reported_by=request.user,
        )

        return Response(self.OutputSerializer(report).data, status=status.HTTP_201_CREATED)
