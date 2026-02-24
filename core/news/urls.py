from django.urls import path
from rest_framework.routers import SimpleRouter

from core.news.apis.comment import EventCommentViewSet
from core.news.apis.follow import FollowViewSet
from core.news.apis.report import EventReportApi
from core.news.apis.story import StoryViewSet
from core.news.apis.source import EventTopPublishersApi, SourceListApi

router = SimpleRouter()
router.register(
    r"events/(?P<event_pk>[^/.]+)/comments",
    EventCommentViewSet,
    basename="event-comments",
)

app_name = "news"
urlpatterns = [
    path(
        "follows/",
        FollowViewSet.as_view({"get": "list", "post": "create", "delete": "destroy"}),
        name="follow",
    ),
    path("reports/", EventReportApi.as_view(), name="event_report"),
    path("sources/", SourceListApi.as_view(), name="source_list"),
    path("events/<int:event_id>/sources/", EventTopPublishersApi.as_view(), name="event_source_list"),
    path("stories/search/", StoryViewSet.as_view({"get": "search"}), name="story_search"),
    path("stories/<str:story_id>/", StoryViewSet.as_view({"get": "retrieve"}), name="story_retrieve"),
] + router.urls
