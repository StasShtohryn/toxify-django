from django.contrib.auth.views import LogoutView, LoginView
from django.urls import path
from . import views

urlpatterns = [
    # Реєстрація
    path("register/", views.RegisterView.as_view(), name="register"),
    path('login/', LoginView.as_view(template_name='profiles/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Профіль
    path("edit/", views.ProfileEditView.as_view(), name="profile_edit"),
    path("users/<str:username>/", views.ProfileDetailView.as_view(), name="profile_detail"),

    # Follow/Unfollow
    path("users/<str:username>/follow/", views.FollowToggleView.as_view(), name="follow_toggle"),
]