from zoneinfo import reset_tzpath

from django.db import transaction
from django.db.models import QuerySet
from .models import BaseUser, Profile


def create_profile(*, user: BaseUser, bio: str | None) -> QuerySet[Profile]:
	return Profile.objects.create(user=user, bio=bio)


def create_user(*, email: str, password: str) -> QuerySet[BaseUser]:
	return BaseUser.objects.create_user(email=email, password=password)

@transaction.atomic
def register(*, email: str, password: str, bio: str | None) -> QuerySet[BaseUser]:
	user = create_user(email=email, password=password)
	create_profile(user=user, bio=bio)
	return user
