from django.urls import path

from core.news.apis.report import EventReportApi


app_name = "news"
urlpatterns = [
    path("reports/", EventReportApi.as_view(), name="event_report"),
]
