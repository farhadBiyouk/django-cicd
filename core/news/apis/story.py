from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import serializers, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core.news.models import Article, EntityMention, Event, EventComment, Follow, Story


class StoryPublisherSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)


class StoryLastSevenDaysSerializer(serializers.Serializer):
    title = serializers.CharField(read_only=True, allow_null=True)
    event_count = serializers.IntegerField(read_only=True)
    publisher_count = serializers.IntegerField(read_only=True)
    article_count = serializers.IntegerField(read_only=True)
    trend_count = serializers.IntegerField(read_only=True)
    summary = serializers.CharField(read_only=True, allow_null=True)


class StorySerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True, allow_null=True)
    published_at = serializers.DateTimeField(read_only=True, allow_null=True)
    last_updated_at = serializers.DateTimeField(read_only=True, allow_null=True)
    categories = serializers.ListField(child=serializers.CharField(), read_only=True)
    last_seven_days = StoryLastSevenDaysSerializer(read_only=True)
    event_count = serializers.IntegerField(read_only=True)
    publisher_count = serializers.IntegerField(read_only=True)
    article_count = serializers.IntegerField(read_only=True)
    trend_count = serializers.IntegerField(read_only=True)
    conflict_count = serializers.IntegerField(read_only=True)
    person_count = serializers.IntegerField(read_only=True)
    entities_count = serializers.IntegerField(read_only=True)
    save_count = serializers.IntegerField(read_only=True)
    view_count = serializers.IntegerField(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    like_count = serializers.IntegerField(read_only=True)
    summary = serializers.CharField(read_only=True, allow_null=True)
    publishers = StoryPublisherSerializer(many=True, read_only=True)
    description = serializers.CharField(read_only=True, allow_null=True)
    album_candidates = serializers.ListField(child=serializers.CharField(), read_only=True)
    article_statistics = serializers.ListField(child=serializers.DictField(), read_only=True)


class StoryListSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True, allow_null=True)
    published_at = serializers.DateTimeField(read_only=True, allow_null=True)
    last_updated_at = serializers.DateTimeField(read_only=True, allow_null=True)
    event_count = serializers.IntegerField(read_only=True)
    publisher_count = serializers.IntegerField(read_only=True)
    article_count = serializers.IntegerField(read_only=True)
    trend_count = serializers.IntegerField(read_only=True)
    summary = serializers.CharField(read_only=True, allow_null=True)


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
    queryset = Story.objects.none()

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

    @staticmethod
    def _to_image_value(value):
        if not value:
            return None
        try:
            return value.url
        except Exception:
            return str(value)

    def _build_article_statistics(self, related_articles_queryset):
        now = timezone.now()
        buckets = {}
        for idx in range(1, 5):
            start = now - timedelta(days=idx * 7)
            end = now - timedelta(days=(idx - 1) * 7)
            web_count = related_articles_queryset.filter(
                created_at__gte=start,
                created_at__lt=end,
            ).count()
            buckets[str(idx)] = {"social": 0, "web": web_count}
        return [buckets]

    def _build_story_payload(self, story):
        related_events = Event.objects.filter(event_stories__story=story).distinct()
        related_articles = Article.objects.filter(event__event_stories__story=story).distinct()

        categories = list(
            story.story_categories.select_related("category").values_list("category__title", flat=True)
        )

        publishers_rows = (
            related_articles.values("news_source_id", "news_source__name")
            .annotate(published_articles_count=Count("id"))
            .order_by("-published_articles_count", "news_source__name")
        )
        publishers = [
            {"id": row["news_source_id"], "name": row["news_source__name"]}
            for row in publishers_rows
            if row["news_source_id"] is not None and row["news_source__name"]
        ]

        unique_album = []
        for image in [
            self._to_image_value(story.image_url),
            *related_events.values_list("image_url", flat=True),
            *related_articles.values_list("image_url", flat=True),
            *related_articles.values_list("remote_image_url", flat=True),
        ]:
            if image and image not in unique_album:
                unique_album.append(image)
            if len(unique_album) >= 3:
                break

        entity_mentions = EntityMention.objects.filter(news_article__in=related_articles).select_related("entity")
        entities_count = entity_mentions.values("entity_id").distinct().count()
        person_count = entity_mentions.filter(entity__entity_type__iexact="person").values("entity_id").distinct().count()

        now = timezone.now()
        seven_days_ago = now - timedelta(days=7)
        events_last_7 = related_events.filter(created_at__gte=seven_days_ago)
        articles_last_7 = related_articles.filter(created_at__gte=seven_days_ago)

        top_event_count = story.event_count if story.event_count is not None else related_events.count()
        top_article_count = story.article_count if story.article_count is not None else related_articles.count()
        top_trend_count = related_events.filter(status=1).count()
        top_conflict_count = related_events.filter(status=2).count()
        related_event_ids = list(related_events.values_list("id", flat=True))
        save_count = Follow.objects.filter(
            target_type=Follow.TARGET_STORY,
            target_id=str(story.id),
        ).count()
        comment_count = EventComment.objects.filter(event_id__in=[str(item) for item in related_event_ids]).count()

        payload = {
            "id": story.id,
            "title": story.title,
            "published_at": story.created_at,
            "last_updated_at": story.updated_at,
            "categories": categories,
            "last_seven_days": {
                "title": story.title,
                "event_count": events_last_7.count(),
                "publisher_count": articles_last_7.values("news_source_id").distinct().count(),
                "article_count": articles_last_7.count(),
                "trend_count": events_last_7.filter(status=1).count(),
                "summary": story.short_summary,
            },
            "event_count": top_event_count,
            "publisher_count": len(publishers),
            "article_count": top_article_count,
            "trend_count": top_trend_count,
            "conflict_count": top_conflict_count,
            "person_count": person_count,
            "entities_count": entities_count,
            "save_count": save_count,
            "view_count": 0,
            "comment_count": comment_count,
            "like_count": 0,
            "summary": story.short_summary,
            "publishers": publishers,
            "description": story.description,
            "album_candidates": unique_album[:3],
            "article_statistics": self._build_article_statistics(related_articles),
        }
        return payload

    def retrieve(self, request, story_id=None):
        story = Story.objects.filter(id=story_id).first()
        if not story:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        payload = self._build_story_payload(story)
        serializer = self.get_serializer(instance=payload)
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

        queryset = Story.objects.all().annotate(
            publisher_count_calc=Count(
                "story_events__event__articles__news_source",
                distinct=True,
            ),
            trend_count_calc=Count(
                "story_events__event",
                filter=Q(story_events__event__status=1),
                distinct=True,
            ),
        )

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

        order_expr = sort_field if sort_order == "asc" else f"-{sort_field}"
        queryset = queryset.order_by(order_expr, "-id")

        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        stories_page = queryset[start:end]

        stories = []
        for story in stories_page:
            stories.append(
                {
                    "id": story.id,
                    "title": story.title,
                    "published_at": story.created_at,
                    "last_updated_at": story.updated_at,
                    "event_count": story.event_count,
                    "publisher_count": story.publisher_count_calc or 0,
                    "article_count": story.article_count,
                    "trend_count": story.trend_count_calc or 0,
                    "summary": story.short_summary,
                }
            )

        serializer = self.get_serializer(stories, many=True)
        return Response({"total": total, "results": serializer.data})
