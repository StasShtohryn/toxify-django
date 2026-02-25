from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

from profiles.views import MyProfileView, register

urlpatterns = [
    path('my_profile/', MyProfileView.as_view(), name='my_profile'),
    path('register/', register, name='register'),
    path('login/', LoginView.as_view(template_name='profiles/login.html'), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
]