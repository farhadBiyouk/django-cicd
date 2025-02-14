from django.urls import path

from .apis.post import PostApi, PostDetailApi
from .apis.subscription import SubscribeApi, SubscribeDeleteApi


app_name = "blog"
urlpatterns = [
        path("subscribe/", SubscribeApi.as_view(), name="subscribe"),
        path("subscribe/<str:email>", SubscribeDeleteApi.as_view(), name="subscribe_detail"),
        path("post/", PostApi.as_view(), name="post"),
        path("post/<slug:slug>", PostDetailApi.as_view(), name="post_detail"),
        ]