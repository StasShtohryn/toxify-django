from django.urls import path

from profiles.views import MyProfileView

urlpatterns = [
    path('my_profile/', MyProfileView.as_view(), name='my_profile'),
]