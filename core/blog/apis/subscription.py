from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from drf_spectacular.utils import extend_schema

from core.blog.services.post import unsubscribe, subscribe
from core.blog.selectors.posts import get_subscribers
from core.blog.models import Post, Subscription
from core.api.pagination import  get_paginated_response, LimitOffsetPagination, get_paginated_response_context
from core.api.mixins import ApiAuthMixin
from core.api.pagination import LimitOffsetPagination



class SubscribeDeleteApi(ApiAuthMixin, APIView):
	def delete(self, request, username):
		try:
			unsubscribe(user=request.user, username=username)
		except Exception as ex:
			return Response({'detail': 'Database Error - ' + str(ex)}, status=status.HTTP_400_BAD_REQUEST)
		
		return Response(status=status.HTTP_204_NO_CONTENT)


class SubscribeApi(ApiAuthMixin, APIView):
	class Pagination(LimitOffsetPagination):
		default_limit = 10
	
	class InputSubSerializer(serializers.Serializer):
		email = serializers.EmailField(max_length=200)
	
	class OutputSubSerializer(serializers.ModelSerializer):
		email = serializers.SerializerMethodField('get_username')
		
		class Meta:
			model = Subscription
			fields = ('email',)
		
		def get_username(self, subscription):
			return subscription.target.email
	@extend_schema(responses=OutputSubSerializer)
	def get(self,request):
		user = request.user
		query = get_subscribers(user=user)
		return get_paginated_response(
			request=request,
			pagination_class=self.Pagination,
			queryset=query,
			serializer_class=self.OutputSubSerializer,
			view=self
		)
		
	@extend_schema(request=InputSubSerializer, responses=OutputSubSerializer)
	def post(self, request):
		ser = self.InputSubSerializer(data=request.data)
		ser.is_valid(raise_exception=True)
		try:
			query = subscribe(user=request.user, email=ser.validated_data['email'])
		
		except Exception as ex:
			return Response({'detail': 'Database Error - ' + str(ex)}, status=status.HTTP_400_BAD_REQUEST)
		
		return Response(self.OutputSubSerializer(query).data, status=status.HTTP_201_CREATED)
