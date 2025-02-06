from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import re


def number_validator(password):
	pattern = re.compile('[0-9]')
	if pattern.search(password) is None:
		raise ValidationError(
			message=_("password must be include number "),
			code='password_include_number'
		)


def letter_validator(password):
	pattern = re.compile('[a-zA-Z]')
	if pattern.search(password) is None:
		raise ValidationError(
			message=_("password must be include letter "),
			code='password_include_number'
		)


def special_char_validator(password):
	pattern = re.compile('[!@#$%^&*(){}<>_-]')
	if pattern.search(password) is None:
		raise ValidationError(
			message=_("password must be include sign "),
			code='password_include_number'
		)
