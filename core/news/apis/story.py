from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core.news.models import Story


class StorySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True, allow_null=True)
    title_last_generated_at = serializers.DateTimeField(read_only=True, allow_null=True)
    description = serializers.CharField(read_only=True, allow_null=True)
    description_last_generated_at = serializers.DateTimeField(read_only=True, allow_null=True)
    short_summary = serializers.CharField(read_only=True)
    detailed_summary = serializers.CharField(read_only=True)
    status = serializers.IntegerField(read_only=True)
    confidence_score = serializers.FloatField(read_only=True)
    event_count = serializers.IntegerField(read_only=True)
    article_count = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    last_event_added_at = serializers.DateTimeField(read_only=True, allow_null=True)
    image_url = serializers.CharField(read_only=True, allow_null=True)


class StoryListSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True, allow_null=True)
    short_summary = serializers.CharField(read_only=True)
    event_count = serializers.IntegerField(read_only=True)
    article_count = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    image_url = serializers.CharField(read_only=True, allow_null=True)
    is_trend = serializers.SerializerMethodField()

    def get_is_trend(self, obj):
        # A story is treated as trending when it has at least one event.
        return (obj.event_count or 0) > 0


@extend_schema_view(
    retrieve=extend_schema(
        tags=["Story data"],
        summary="مشاهده استوری",
        description="جزئیات یک استوری با story_id",
        responses=StorySerializer,
    ),
    search=extend_schema(
        tags=["Story data"],
        summary="جستجوی استوری‌ها",
        description="لیست استوری‌ها با فیلتر و مرتب‌سازی",
        responses=StoryListSerializer(many=True),
    ),
)
class StoryViewSet(GenericViewSet):
    serializer_class = StorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    queryset = Story.objects.all()

    def get_serializer_class(self):
        if self.action == "search":
            return StoryListSerializer
        return self.serializer_class

    @staticmethod
    def _to_int(value, default, min_value=None, max_value=None):
        try:
            num = int(value)
        except (TypeError, ValueError):
            num = default
        if min_value is not None:
            num = max(num, min_value)
        if max_value is not None:
            num = min(num, max_value)
        return num

    @staticmethod
    def _to_bool(value):
        if value in (None, ""):
            return None
        lowered = str(value).strip().lower()
        if lowered in {"1", "true", "t", "yes", "y"}:
            return True
        if lowered in {"0", "false", "f", "no", "n"}:
            return False
        raise ValueError("is_trend must be a boolean (true/false)")

    def retrieve(self, request, story_id=None):
        story = Story.objects.filter(id=story_id).first()
        if not story:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(instance=story)
        return Response(serializer.data)

    @extend_schema(
        tags=["Story data"],
        parameters=[
            OpenApiParameter("query", description="متن جستجو", required=False, type=str),
            OpenApiParameter("page", description="شماره صفحه", required=False, type=int, default=1),
            OpenApiParameter("page_size", description="تعداد رکورد", required=False, type=int, default=20),
            OpenApiParameter(
                "is_trend",
                description="فیلتر روندی بودن (براساس event_count > 0)",
                required=False,
                type=bool,
            ),
            OpenApiParameter("event_id", description="فیلتر بر اساس event_id", required=False, type=int),
            OpenApiParameter(
                "sort_field",
                description="فیلد مرتب‌سازی (created_at | event_count)",
                required=False,
                type=str,
                default="created_at",
            ),
            OpenApiParameter("sort_order", description="asc یا desc", required=False, type=str, default="desc"),
        ],
        responses=StoryListSerializer(many=True),
    )
    @action(detail=False, methods=["get"])
    def search(self, request):
        query = request.query_params.get("query")
        page = self._to_int(request.query_params.get("page"), default=1, min_value=1)
        page_size = self._to_int(
            request.query_params.get("page_size"),
            default=20,
            min_value=1,
            max_value=100,
        )
        sort_field = request.query_params.get("sort_field", "created_at")
        sort_order = request.query_params.get("sort_order", "desc").strip().lower()
        event_id = request.query_params.get("event_id")
        is_trend = request.query_params.get("is_trend")

        queryset = Story.objects.all()

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(short_summary__icontains=query)
                | Q(detailed_summary__icontains=query)
            )

        if event_id not in (None, ""):
            try:
                event_id_int = int(event_id)
            except ValueError:
                return Response(
                    {"detail": "event_id must be an integer"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = queryset.filter(story_events__event_id=event_id_int)

        if is_trend not in (None, ""):
            try:
                is_trend_bool = self._to_bool(is_trend)
            except ValueError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            if is_trend_bool:
                queryset = queryset.filter(event_count__gt=0)
            else:
                queryset = queryset.filter(event_count=0)

        queryset = queryset.distinct()

        allowed_sort_fields = {"created_at", "event_count"}
        if sort_field not in allowed_sort_fields:
            sort_field = "created_at"
        if sort_order not in {"asc", "desc"}:
            sort_order = "desc"

        order_expression = sort_field if sort_order == "asc" else f"-{sort_field}"
        queryset = queryset.order_by(order_expression, "-id")

        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        stories = queryset[start:end]

        serializer = self.get_serializer(stories, many=True)
        return Response({"total": total, "results": serializer.data})
