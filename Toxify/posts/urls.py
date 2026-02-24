from posts.views import PostsListView, PostCreateView
from django.urls import path, include

urlpatterns = [
    path('', PostsListView.as_view(), name='posts'),
    path('create/', PostCreateView.as_view(), name='post_create'),
]