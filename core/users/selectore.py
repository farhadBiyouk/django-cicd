from .models import Profile, BaseUser


def get_profile(*,user: BaseUser) -> BaseUser:
	return Profile.objects.get(user=user)
