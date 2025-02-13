from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from drf_spectacular.utils import extend_schema
from django.core.validators import MinLengthValidator
from rest_framework_simplejwt.serializers import RefreshToken

from core.api.pagination import LimitOffsetPagination
from core.users.services import register
from core.users.selectore import get_profile
from core.users.models import BaseUser, Profile
from core.users.validator import number_validator, letter_validator, special_char_validator
from core.api.mixins import ApiAuthMixin


class RegisterApi(APIView):
	class Pagination(LimitOffsetPagination):
		default_limit = 15
	
	class InputRegisterSerializer(serializers.Serializer):
		email = serializers.EmailField(max_length=255)
		bio = serializers.CharField(max_length=255)
		password = serializers.CharField(validators=[
			MinLengthValidator(limit_value=10),
			number_validator,
			letter_validator,
			special_char_validator
		])
		confirm_password = serializers.CharField(max_length=255)
		
		def validate_email(self, email):
			if BaseUser.objects.filter(email=email).exists():
				raise serializers.ValidationError('email already taken')
			return email
		
		def validate(self, data):
			if not data.get('password') or not data.get('confirm_password'):
				raise serializers.ValidationError('Please enter password and confirm password')
			if data.get('password') != data.get('confirm_password'):
				raise serializers.ValidationError('password and confirm password not match')
			return data
	
	class OutputRegisterSerializer(serializers.ModelSerializer):
		token = serializers.SerializerMethodField('get_token')
		
		class Meta:
			model = BaseUser
			fields = ('email', 'token', 'created_at', 'updated_at')
		
		def get_token(self, user):
			data = dict()
			token_class = RefreshToken
			
			refresh = token_class.for_user(user)
			data['refresh'] = str(refresh)
			data['access'] = str(refresh.access_token)
			return data
	
	@extend_schema(request=InputRegisterSerializer, responses=OutputRegisterSerializer)
	def post(self, request):
		ser = self.InputRegisterSerializer(data=request.data)
		ser.is_valid(raise_exception=True)
		try:
			query = register(
				email=ser.validated_data.get('email'),
				password=ser.validated_data.get('password'),
				bio=ser.validated_data.get('bio')
			)
		except Exception as ex:
			return Response(f'Database error {ex}', status=status.HTTP_400_BAD_REQUEST)
		return Response(self.OutputRegisterSerializer(query, context={"request": request}).data,
		                status=status.HTTP_201_CREATED)


class ProfileApi(ApiAuthMixin, APIView):
	class OutputProfileSerializer(serializers.ModelSerializer):
		class Meta:
			model = Profile
			fields = (
				"user",
				"post_count",
				"subscriber_count",
				"subscription_count",
				"bio",
			)
	
	@extend_schema(responses=OutputProfileSerializer)
	def get(self, request):
		query = get_profile(user=request.user)
		return Response(self.OutputProfileSerializer(query, context={"request": request}).data,
		                status=status.HTTP_200_OK)
