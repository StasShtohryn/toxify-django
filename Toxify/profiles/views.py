from django.shortcuts import render
from django.views.generic import ListView, TemplateView

from profiles.models import Profile


# Create your views here.
class MyProfileView(TemplateView):
    model = Profile
    template_name = 'profiles/my-profile.html'
    context_object_name = 'my_profile'
