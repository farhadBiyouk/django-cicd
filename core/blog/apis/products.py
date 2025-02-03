from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from drf_spectacular.utils import extend_schema

from core.api.pagination import LimitOffsetPagination
from core.blog.models import Product
from core.blog.selectors.products import get_products
from core.blog.services.products import create_product


class ProductApi(APIView):
	class Pagination(LimitOffsetPagination):
		default_limit = 15
	
	class InputSerializer(serializers.Serializer):
		name = serializers.CharField(max_length=255)
	
	class OutputSerializer(serializers.ModelSerializer):
		class Meta:
			model = Product
			fields = ('name', 'created_at', 'updated_at')
	
	@extend_schema(responses=OutputSerializer)
	def get(self, request):
		query = get_products()
		return Response(self.OutputSerializer(query, many=True, context={"request": request}).data,
		                status=status.HTTP_200_OK)
	
	@extend_schema(request=InputSerializer, responses=OutputSerializer)
	def post(self, request):
		ser = self.InputSerializer(data=request.data)
		ser.is_valid(raise_exception=True)
		try:
			query = create_product(name=ser.validated_data.get('name'))
		except Exception as ex:
			return Response(f'Database error {ex}', status=status.HTTP_400_BAD_REQUEST)
		return Response(self.OutputSerializer(query, context={"request": request}).data, status=status.HTTP_201_CREATED)
