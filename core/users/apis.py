from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from drf_spectacular.utils import extend_schema
from django.core.validators import MinLengthValidator

from core.api.pagination import LimitOffsetPagination
from core.users.services.products import create_user
from core.users.models import BaseUser
from core.users.validator import number_validator, letter_validator, special_char_validator


class RegisterApi(APIView):
	class Pagination(LimitOffsetPagination):
		default_limit = 15
	
	class InputRegisterSerializer(serializers.Serializer):
		email = serializers.EmailField(max_length=255)
		password = serializers.CharField(validators=[
			MinLengthValidator(limit_value=10),
			number_validator,
			letter_validator,
			special_char_validator
		])
		confirm_password = serializers.CharField(max_length=255)
	
	class OutputRegisterSerializer(serializers.ModelSerializer):
		class Meta:
			model = BaseUser
			fields = ('name', 'created_at', 'updated_at')
	
	@extend_schema(request=InputRegisterSerializer, responses=OutputRegisterSerializer)
	def post(self, request):
		ser = self.InputRegisterSerializer(data=request.data)
		ser.is_valid(raise_exception=True)
		try:
			query = create_user(name=ser.validated_data.get('name'))
		except Exception as ex:
			return Response(f'Database error {ex}', status=status.HTTP_400_BAD_REQUEST)
		return Response(self.OutputRegisterSerializer(query, context={"request": request}).data,
		                status=status.HTTP_201_CREATED)
