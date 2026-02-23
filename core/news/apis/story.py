from django.conf import settings
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core.news.es_helper import ESHelper


class StorySerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    doc_id = serializers.SerializerMethodField()
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
    is_trend = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.get("id") or obj.get("doc_id") or obj.get("_id")

    def get_doc_id(self, obj):
        return obj.get("doc_id") or obj.get("_id")

    def get_is_trend(self, obj):
        trend_value = obj.get("is_trend")
        if isinstance(trend_value, bool):
            return trend_value
        try:
            return int(obj.get("event_count") or 0) > 0
        except (TypeError, ValueError):
            return False


class StoryListSerializer(serializers.Serializer):
    id = serializers.SerializerMethodField()
    doc_id = serializers.SerializerMethodField()
    title = serializers.CharField(read_only=True, allow_null=True)
    short_summary = serializers.CharField(read_only=True)
    event_count = serializers.IntegerField(read_only=True)
    article_count = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    image_url = serializers.CharField(read_only=True, allow_null=True)
    is_trend = serializers.SerializerMethodField()

    def get_id(self, obj):
        return obj.get("id") or obj.get("doc_id") or obj.get("_id")

    def get_doc_id(self, obj):
        return obj.get("doc_id") or obj.get("_id")

    def get_is_trend(self, obj):
        trend_value = obj.get("is_trend")
        if isinstance(trend_value, bool):
            return trend_value
        try:
            return int(obj.get("event_count") or 0) > 0
        except (TypeError, ValueError):
            return False


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
    lookup_field = "doc_id"
    queryset = []

    STORY_SORT_MAP = {
        "created_at": {"field": "created_at", "unmapped_type": "date"},
        "event_count": {"field": "event_count", "unmapped_type": "long"},
        "title": {"field": "title.keyword", "unmapped_type": "keyword"},
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        index_name = getattr(settings, "INDEX_STORY_NAME", "story")
        self.es_helper = ESHelper(index_name)

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
        story = self.es_helper.get(story_id)
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
                description="فیلتر روندی بودن",
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

        filters = {}
        extra_filter_clauses = []
        if event_id not in (None, ""):
            try:
                event_id_int = int(event_id)
            except ValueError:
                return Response(
                    {"detail": "event_id must be an integer"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            filters["event_id"] = event_id_int

        if is_trend not in (None, ""):
            try:
                is_trend_bool = self._to_bool(is_trend)
            except ValueError as exc:
                return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            if is_trend_bool:
                extra_filter_clauses.append({"range": {"event_count": {"gt": 0}}})
            else:
                extra_filter_clauses.append({"term": {"event_count": 0}})

        raw_hits, total = self.es_helper.search(
            query=query,
            page=page,
            page_size=page_size,
            sort_field=sort_field,
            sort_order=sort_order,
            filters=filters or None,
            sort_map=self.STORY_SORT_MAP,
            default_sort_field="created_at",
            search_fields=["title", "description", "short_summary", "detailed_summary"],
            extra_filter_clauses=extra_filter_clauses,
        )

        stories = []
        for hit in raw_hits:
            doc = hit.get("_source", {})
            doc["_id"] = hit.get("_id")
            if "doc_id" not in doc:
                doc["doc_id"] = hit.get("_id")
            stories.append(doc)

        serializer = self.get_serializer(stories, many=True)
        return Response({"total": total, "results": serializer.data})
