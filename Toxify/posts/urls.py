from . import views
from .views import PostsListView, PostCreateView, SearchView, CommentCreateView, PostDetailView, LikePostToggleView
from django.urls import path, include

urlpatterns = [
    path('', PostsListView.as_view(), name='posts'),
    path('search/', SearchView.as_view(), name='search'),
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('create/<str:username>/', PostCreateView.as_view(), name='post_create'),
    path('post/<int:post_id>', PostDetailView.as_view(), name='post_detail'),
    path('post/<int:post_id>/comment/<str:username>/', CommentCreateView.as_view(), name='comment_create'),
    path('post/<int:post_id>/report/', views.report_post, name='report_post'),
    path('post/<int:post_id>/like/', LikePostToggleView.as_view(), name='like_post_toggle'),
]