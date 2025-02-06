from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.models import BaseUserManager as BUM
from core.common.models import BaseModel


class BaseUserManager(BUM):
	def create_user(self, email, password, **extera_kwargs):
		if not email:
			raise ValueError('the email must be set .')
		user = self.model(email=self.normalize_email(email), **extera_kwargs)
		user.set_password(password)
		user.save(using=self._db)
		return user
	
	def create_superuser(self, email, password, **extera_kwargs):
		extera_kwargs.setdefault('is_admin', True)
		extera_kwargs.setdefault('is_superuser', True)
		
		if extera_kwargs.get('is_admin') is not True:
			raise ValueError('superuser have admin true')
		if extera_kwargs.get("is_superuser") is not True:
			raise ValueError("Superuser must have is_superuser=True.")
		return self.create_user(email, password, **extera_kwargs)


class BaseUser(BaseModel, AbstractBaseUser, PermissionsMixin):
	email = models.EmailField(max_length=255, unique=True)
	is_active = models.BooleanField(default=True)
	is_admin = models.BooleanField(default=False)
	
	USERNAME_FIELD = 'email'
	
	objects = BaseUserManager()
	
	def __str__(self):
		return self.email
	
	def is_staff(self):
		return self.is_admin


class Profile(models.Model):
	user = models.OneToOneField(BaseUser, on_delete=models.CASCADE)
	post_count = models.PositiveIntegerField(default=0)
	subscriber_count = models.PositiveIntegerField(default=0)
	subscription_count = models.PositiveIntegerField(default=0)
	bio = models.CharField(max_length=1000, null=True, blank=True)
	
	def __str__(self):
		return f'{self.user} >> {self.bio}'