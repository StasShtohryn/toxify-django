from .views import PostsListView, PostCreateView, SearchView
from django.urls import path, include

urlpatterns = [
    path('', PostsListView.as_view(), name='posts'),
    path('search/', SearchView.as_view(), name='search'),
    path('create/<str:username>/', PostCreateView.as_view(), name='post_create'),
]