from .views import PostsListView, PostCreateView
from django.urls import path, include

urlpatterns = [
    path('', PostsListView.as_view(), name='posts'),
    path('create/<str:username>/', PostCreateView.as_view(), name='post_create'),
]