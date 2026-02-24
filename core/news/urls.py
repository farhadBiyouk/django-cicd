from django.urls import path
from rest_framework.routers import SimpleRouter

from core.news.apis.comment import EventCommentViewSet
from core.news.apis.report import EventReportApi
from core.news.apis.story import StoryViewSet

router = SimpleRouter()
router.register(
    r"events/(?P<event_pk>[^/.]+)/comments",
    EventCommentViewSet,
    basename="event-comments",
)

app_name = "news"
urlpatterns = [
    path("reports/", EventReportApi.as_view(), name="event_report"),
    path("stories/search/", StoryViewSet.as_view({"get": "search"}), name="story_search"),
    path("stories/<str:story_id>/", StoryViewSet.as_view({"get": "retrieve"}), name="story_retrieve"),
] + router.urls
