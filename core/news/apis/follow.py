from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core.api.mixins import ApiAuthMixin
from core.news.models import Entity, Event, Follow, Source, Story
from core.news.serializers import (
    FollowListQuerySerializer,
    FollowMutationSerializer,
    FollowSerializer,
)


@extend_schema_view(
    list=extend_schema(
        tags=["Follow data"],
        summary="لیست دنبال‌کرده‌ها",
        description="لیست مواردی که کاربر دنبال کرده است",
        parameters=[
            OpenApiParameter("page", description="شماره صفحه", required=False, type=int, default=1),
            OpenApiParameter("page_size", description="تعداد رکورد", required=False, type=int, default=20),
            OpenApiParameter("target_type", description="نوع موجودیت", required=False, type=str),
        ],
        responses=FollowSerializer(many=True),
    ),
    create=extend_schema(
        tags=["Follow data"],
        summary="دنبال‌کردن موجودیت",
        description="دنبال‌کردن رویداد، پرونده، شخص، ناشر یا سایر موجودیت",
        request=FollowMutationSerializer,
        responses=FollowSerializer,
    ),
    destroy=extend_schema(
        tags=["Follow data"],
        summary="لغو دنبال‌کردن",
        description="لغو دنبال‌کردن یک موجودیت",
        request=FollowMutationSerializer,
        responses={204: None},
    ),
)
class FollowViewSet(ApiAuthMixin, mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet):
    serializer_class = FollowSerializer
    queryset = Follow.objects.none()

    def get_serializer_class(self):
        if self.action == "create":
            return FollowMutationSerializer
        return FollowSerializer

    @staticmethod
    def _parse_target_id(target_id):
        try:
            return int(target_id)
        except (TypeError, ValueError):
            return None

    def _target_exists(self, target_type, target_id):
        target_id_int = self._parse_target_id(target_id)
        if target_id_int is None:
            return False

        if target_type == Follow.TARGET_EVENT:
            return Event.objects.filter(id=target_id_int).exists()
        if target_type == Follow.TARGET_STORY:
            return Story.objects.filter(id=target_id_int).exists()
        if target_type == Follow.TARGET_SOURCE:
            return Source.objects.filter(id=target_id_int).exists()
        if target_type == Follow.TARGET_PERSON:
            return Entity.objects.filter(id=target_id_int, entity_type__iexact="person").exists()
        if target_type == Follow.TARGET_ENTITY:
            return Entity.objects.filter(id=target_id_int).exists()
        return False

    def list(self, request, *args, **kwargs):
        serializer = FollowListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        page = serializer.validated_data["page"]
        page_size = serializer.validated_data["page_size"]
        target_type = serializer.validated_data.get("target_type")

        queryset = Follow.objects.filter(user_id=request.user.id).order_by("-id")
        if target_type:
            queryset = queryset.filter(target_type=target_type)

        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        records = queryset[start:end]

        out_serializer = FollowSerializer(records, many=True)
        return Response({"total": total, "results": out_serializer.data}, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_type = serializer.validated_data["target_type"]
        target_id = serializer.validated_data["target_id"]

        if not self._target_exists(target_type, target_id):
            return Response(
                {"target_id": [f"{target_type} with this id does not exist"]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        follow, created = Follow.objects.get_or_create(
            user_id=request.user.id,
            target_type=target_type,
            target_id=target_id,
        )
        out_serializer = FollowSerializer(follow)
        return Response(
            out_serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        payload = request.data if request.data else request.query_params
        serializer = FollowMutationSerializer(data=payload)
        serializer.is_valid(raise_exception=True)

        deleted_count, _ = Follow.objects.filter(
            user_id=request.user.id,
            target_type=serializer.validated_data["target_type"],
            target_id=serializer.validated_data["target_id"],
        ).delete()

        if deleted_count == 0:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(status=status.HTTP_204_NO_CONTENT)
