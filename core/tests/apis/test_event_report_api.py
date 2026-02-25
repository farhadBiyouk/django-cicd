import json

import pytest
from django.test import Client
from django.urls import reverse

from core.news.apis.report import EventReportApi
from core.news.models import EventReport


@pytest.mark.django_db
def test_event_report_requires_auth():
    client = Client()
    url_ = reverse("api:news:event_report")

    response = client.post(
        url_,
        json.dumps({"event_id": 101, "reason": "Wrong event grouping"}),
        content_type="application/json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_event_report_create_success(api_client, monkeypatch):
    monkeypatch.setattr(EventReportApi, "_event_exists_in_es", lambda self, event_id: True)
    url_ = reverse("api:news:event_report")

    response = api_client.post(
        url_,
        data={"event_id": 101, "reason": "Contains misinformation"},
        format="json",
    )

    data = response.json()

    assert response.status_code == 201
    assert data["event_id"] == 101
    assert data["reason"] == "Contains misinformation"
    assert "reported_by_id" in data
    assert EventReport.objects.filter(event=101).count() == 1


@pytest.mark.django_db
def test_event_report_create_invalid_event(api_client, monkeypatch):
    monkeypatch.setattr(EventReportApi, "_event_exists_in_es", lambda self, event_id: False)
    url_ = reverse("api:news:event_report")

    response = api_client.post(
        url_,
        data={"event_id": 999999, "reason": "Invalid event test"},
        format="json",
    )

    assert response.status_code == 400
    assert "event_id" in response.json()


@pytest.mark.django_db
def test_event_report_list_success(api_client, monkeypatch):
    monkeypatch.setattr(EventReportApi, "_event_exists_in_es", lambda self, event_id: True)
    url_ = reverse("api:news:event_report")

    create_resp_1 = api_client.post(
        url_,
        data={"event_id": 201, "reason": "First report"},
        format="json",
    )
    create_resp_2 = api_client.post(
        url_,
        data={"event_id": 202, "reason": "Second report"},
        format="json",
    )

    assert create_resp_1.status_code == 201
    assert create_resp_2.status_code == 201

    response = api_client.get(url_, {"event_id": 201}, format="json")
    data = response.json()

    assert response.status_code == 200
    assert data["total"] == 1
    assert len(data["results"]) == 1
    assert data["results"][0]["event_id"] == 201
