from django.urls import path, include

urlpatterns = [
    path('blog/', include(('core.blog.urls', 'blog'))),
    path('users/', include(('core.users.urls', 'users'))),
]
