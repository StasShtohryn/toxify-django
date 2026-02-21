from django.shortcuts import render
from django.views.generic import TemplateView, CreateView, UpdateView, ListView

# Create your views here.
class IndexView(TemplateView):
    template_name = 'posts/index.html'
