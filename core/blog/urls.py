from django.urls import path
from core.blog.apis import products

urlpatterns = [
    path('blog/', products.ProductApi.as_view(), name='produce')
]
