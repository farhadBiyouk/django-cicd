from django.conf import settings
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core.news.es_helper import ESHelper
from core.news.models import EventComment
from core.news.serializers import (
    EventCommentCreateSerializer,
    EventCommentReplySerializer,
    EventCommentSerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=["Event comments"],
        summary="گرفتن لیست کامنت‌های یک رویداد",
        description="لیست کامنت‌ها و ریپلای‌های یک رویداد",
        parameters=[
            OpenApiParameter("event_pk", type=str, location=OpenApiParameter.PATH),
        ],
        responses=EventCommentSerializer(many=True),
    ),
    create=extend_schema(
        tags=["Event comments"],
        summary="ثبت کامنت برای یک رویداد",
        description="ثبت یک کامنت جدید در یک رویداد",
        parameters=[
            OpenApiParameter("event_pk", type=str, location=OpenApiParameter.PATH),
        ],
        request=EventCommentCreateSerializer,
        responses=EventCommentSerializer,
    ),
)
class EventCommentViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = EventCommentSerializer
    queryset = EventComment.objects.none()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.event_es_helper = ESHelper(
            getattr(settings, "INDEX_NAME2", getattr(settings, "INDEX_EVENT_NAME", "event"))
        )

    def get_serializer_class(self):
        if self.action == "create":
            return EventCommentCreateSerializer
        if self.action == "reply":
            return EventCommentReplySerializer
        return EventCommentSerializer

    def get_queryset(self):
        event_pk = str(self.kwargs.get("event_pk"))
        return EventComment.objects.filter(event_id=event_pk).order_by("created_at", "id")

    def _event_exists_in_es(self, event_id):
        if self.event_es_helper.get(str(event_id)):
            return True

        body = {
            "size": 1,
            "track_total_hits": True,
            "query": {
                "bool": {
                    "should": [
                        {"term": {"id": event_id}},
                        {"term": {"event_id": event_id}},
                        {"term": {"doc_id": str(event_id)}},
                        {"term": {"doc_id.keyword": str(event_id)}},
                        {"term": {"id.keyword": str(event_id)}},
                    ],
                    "minimum_should_match": 1,
                }
            },
        }
        try:
            res = self.event_es_helper.client.search(index=self.event_es_helper.index, body=body)
        except Exception:
            return False
        total_raw = res.get("hits", {}).get("total", 0)
        total = total_raw.get("value", 0) if isinstance(total_raw, dict) else total_raw
        return total > 0

    @staticmethod
    def _can_moderate(user):
        return bool(getattr(user, "is_admin", False) or getattr(user, "is_superuser", False))

    def _build_tree(self, comments):
        children_map = {}
        roots = []
        for comment in comments:
            if comment.reply_to:
                children_map.setdefault(comment.reply_to, []).append(comment)
            else:
                roots.append(comment)
        return roots, children_map

    def _get_event_comment(self, event_pk, pk):
        return EventComment.objects.filter(id=pk, event_id=str(event_pk)).first()

    def list(self, request, *args, **kwargs):
        comments = list(self.get_queryset())
        roots, children_map = self._build_tree(comments)
        serializer = EventCommentSerializer(roots, many=True, context={"children_map": children_map})
        return Response({"total": len(roots), "results": serializer.data}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        event_pk = str(self.kwargs.get("event_pk"))
        if not self._event_exists_in_es(event_pk):
            return Response(
                {"event_id": ["event with this id does not exist in elasticsearch"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = EventComment.objects.create(
            event_id=event_pk,
            content=serializer.validated_data["content"],
            author_id=request.user.id,
        )
        response_serializer = EventCommentSerializer(comment, context={"children_map": {}})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["Event comments"],
        summary="ثبت ریپلای برای کامنت",
        description="ثبت یک ریپلای برای یک کامنت در یک رویداد",
        parameters=[
            OpenApiParameter("event_pk", type=str, location=OpenApiParameter.PATH),
            OpenApiParameter("pk", type=int, location=OpenApiParameter.PATH),
        ],
        request=EventCommentReplySerializer,
        responses=EventCommentSerializer,
    )
    @action(detail=True, methods=["post"])
    def reply(self, request, event_pk=None, pk=None):
        parent_comment = self._get_event_comment(event_pk, pk)
        if not parent_comment:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        reply_comment = EventComment.objects.create(
            event_id=str(event_pk),
            content=serializer.validated_data["content"],
            author_id=request.user.id,
            reply_to=parent_comment.id,
        )
        response_serializer = EventCommentSerializer(reply_comment, context={"children_map": {}})
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["Event comments"],
        summary="تایید کامنت",
        description="تایید یک کامنت توسط مدیر",
        parameters=[
            OpenApiParameter("event_pk", type=str, location=OpenApiParameter.PATH),
            OpenApiParameter("pk", type=int, location=OpenApiParameter.PATH),
        ],
        responses=EventCommentSerializer,
    )
    @action(detail=True, methods=["post"])
    def approve(self, request, event_pk=None, pk=None):
        if not self._can_moderate(request.user):
            return Response({"detail": "permission denied"}, status=status.HTTP_403_FORBIDDEN)

        comment = self._get_event_comment(event_pk, pk)
        if not comment:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        comment.status = EventComment.STATUS_APPROVED
        comment.save(update_fields=["status", "updated_at"])
        serializer = EventCommentSerializer(comment, context={"children_map": {}})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Event comments"],
        summary="رد کامنت",
        description="رد یک کامنت توسط مدیر",
        parameters=[
            OpenApiParameter("event_pk", type=str, location=OpenApiParameter.PATH),
            OpenApiParameter("pk", type=int, location=OpenApiParameter.PATH),
        ],
        responses=EventCommentSerializer,
    )
    @action(detail=True, methods=["post"])
    def reject(self, request, event_pk=None, pk=None):
        if not self._can_moderate(request.user):
            return Response({"detail": "permission denied"}, status=status.HTTP_403_FORBIDDEN)

        comment = self._get_event_comment(event_pk, pk)
        if not comment:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)

        comment.status = EventComment.STATUS_REJECTED
        comment.save(update_fields=["status", "updated_at"])
        serializer = EventCommentSerializer(comment, context={"children_map": {}})
        return Response(serializer.data, status=status.HTTP_200_OK)
