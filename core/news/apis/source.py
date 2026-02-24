from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from core.news.models import Source
from core.news.serializers.source import SourceListQuerySerializer, SourceListSerializer


class SourceListApi(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        tags=["Source data"],
        summary="لیست ناشران",
        description="گرفتن لیست ناشران با جستجو و فیلتر",
        parameters=[
            OpenApiParameter("page", description="شماره صفحه", required=False, type=int, default=1),
            OpenApiParameter("page_size", description="تعداد رکورد", required=False, type=int, default=20),
            OpenApiParameter("search", description="جستجو در نام و نام نرمال", required=False, type=str),
            OpenApiParameter("status", description="فیلتر وضعیت", required=False, type=int),
            OpenApiParameter("is_verified", description="فیلتر تایید ناشر", required=False, type=bool),
        ],
        responses=SourceListSerializer(many=True),
    )
    def get(self, request):
        query_serializer = SourceListQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        page = query_serializer.validated_data["page"]
        page_size = query_serializer.validated_data["page_size"]
        search = query_serializer.validated_data.get("search")
        status_filter = query_serializer.validated_data.get("status")
        is_verified = query_serializer.validated_data.get("is_verified")

        queryset = Source.objects.all().order_by("-id")

        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(normalized_name__icontains=search)
            )

        if status_filter is not None:
            queryset = queryset.filter(status=status_filter)

        if is_verified is not None:
            queryset = queryset.filter(is_verified=is_verified)

        total = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        sources = queryset[start:end]

        serializer = SourceListSerializer(sources, many=True, context={"request": request})
        return Response({"total": total, "results": serializer.data}, status=status.HTTP_200_OK)
