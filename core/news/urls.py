from django.urls import path

from core.news.apis.report import EventReportApi
from core.news.apis.story import StoryViewSet


app_name = "news"
urlpatterns = [
    path("reports/", EventReportApi.as_view(), name="event_report"),
    path("stories/search/", StoryViewSet.as_view({"get": "search"}), name="story_search"),
    path("stories/<int:story_id>/", StoryViewSet.as_view({"get": "retrieve"}), name="story_retrieve"),
]
