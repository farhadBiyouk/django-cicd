from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.api.mixins import ApiAuthMixin
from core.news.models import EventReport
from core.news.serializers import (
    EventReportCreateSerializer,
    EventReportQuerySerializer,
    EventReportSerializer,
)


@extend_schema_view(
    get=extend_schema(
        tags=["news"],
        summary="List event reports",
        description="List reports with optional event_id filter",
        parameters=[
            OpenApiParameter("page", description="Page number", required=False, type=int, default=1),
            OpenApiParameter("page_size", description="Page size", required=False, type=int, default=20),
            OpenApiParameter("event_id", description="Filter by event id", required=False, type=int),
        ],
        responses=EventReportSerializer(many=True),
    ),
    post=extend_schema(
        tags=["news"],
        summary="Submit event report",
        description="Create a report for an event using event_id and reason",
        request=EventReportCreateSerializer,
        responses=EventReportSerializer,
    ),
)
class EventReportApi(ApiAuthMixin, APIView):
    def get(self, request):
        query_serializer = EventReportQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        page = query_serializer.validated_data["page"]
        page_size = query_serializer.validated_data["page_size"]
        event_id = query_serializer.validated_data.get("event_id")

        queryset = EventReport.objects.all().order_by("-id")
        if event_id:
            queryset = queryset.filter(event=event_id)

        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        reports = queryset[start:end]

        serializer = EventReportSerializer(reports, many=True)
        return Response({"total": total, "results": serializer.data}, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = EventReportCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        report = EventReport.objects.create(
            event=serializer.validated_data["event_id"],
            reason=serializer.validated_data["reason"],
            reported_by=request.user.id,
        )

        return Response(EventReportSerializer(report).data, status=status.HTTP_201_CREATED)
