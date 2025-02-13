from django.db import transaction
from django.core.cache import cache

from .models import BaseUser, Profile


def create_profile(*, user: BaseUser, bio: str | None) -> Profile:
	return Profile.objects.create(user=user, bio=bio)


def create_user(*, email: str, password: str) -> BaseUser:
	return BaseUser.objects.create_user(email=email, password=password)


@transaction.atomic
def register(*, email: str, password: str, bio: str | None) -> BaseUser:
	user = create_user(email=email, password=password)
	create_profile(user=user, bio=bio)
	return user


def profile_count_update():
	
	profiles = cache.keys("profile_*")
	
	for profile_key in profiles:  # profile_amirbahador.pv@gmail.com
		email = profile_key.replace("profile_", "")
		data = cache.get(profile_key)
		
		try:
			profile = Profile.objects.get(user__email=email)
			profile.post_count = data.get("post_count")
			profile.subscriber_count = data.get("subscriber_count")
			profile.subscription_count = data.get("subscription_count")
			profile.save()
		
		except Exception as ex:
			print(ex)