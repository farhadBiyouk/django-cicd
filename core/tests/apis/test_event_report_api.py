import json

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from core.news.models import Event, EventReport


def create_event():
    now = timezone.now()
    return Event.objects.create(
        title="Breaking event",
        short_summary="Short summary",
        detailed_summary="Detailed summary",
        status=1,
        confidence_score=0.9,
        article_count=0,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.django_db
def test_event_report_requires_auth():
    event = create_event()
    client = Client()
    url_ = reverse("api:news:event_report")

    response = client.post(
        url_,
        json.dumps({"event_id": event.id, "reason": "Wrong event grouping"}),
        content_type="application/json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_event_report_create_success(api_client):
    event = create_event()
    url_ = reverse("api:news:event_report")

    response = api_client.post(
        url_,
        data={"event_id": event.id, "reason": "Contains misinformation"},
        format="json",
    )

    data = response.json()

    assert response.status_code == 201
    assert data["event_id"] == event.id
    assert data["reason"] == "Contains misinformation"
    assert "reported_by_id" in data
    assert EventReport.objects.filter(event=event.id).count() == 1


@pytest.mark.django_db
def test_event_report_create_invalid_event(api_client):
    url_ = reverse("api:news:event_report")

    response = api_client.post(
        url_,
        data={"event_id": 999999, "reason": "Invalid event test"},
        format="json",
    )

    assert response.status_code == 400
    assert "event_id" in response.json()


@pytest.mark.django_db
def test_event_report_list_success(api_client):
    event1 = create_event()
    event2 = create_event()
    url_ = reverse("api:news:event_report")

    create_resp_1 = api_client.post(
        url_,
        data={"event_id": event1.id, "reason": "First report"},
        format="json",
    )
    create_resp_2 = api_client.post(
        url_,
        data={"event_id": event2.id, "reason": "Second report"},
        format="json",
    )

    assert create_resp_1.status_code == 201
    assert create_resp_2.status_code == 201

    response = api_client.get(url_, {"event_id": event1.id}, format="json")
    data = response.json()

    assert response.status_code == 200
    assert data["total"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["event_id"] == event1.id
