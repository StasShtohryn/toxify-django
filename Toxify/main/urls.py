from django.contrib.auth.views import LogoutView
from django.urls import path, include
from .views import AboutUsView

urlpatterns = [
    path('about/', AboutUsView.as_view(), name='about_us'),
]