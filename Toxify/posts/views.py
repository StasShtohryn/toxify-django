from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, TemplateView
from django.db.models import Q

from .models import Post, Hashtag
from profiles.models import Profile, User


# Create your views here.

class SearchView(TemplateView):
    template_name = 'posts/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        context['query'] = query

        if query:
            context['posts'] = Post.objects.filter(
                Q(title__icontains=query) | Q(body__icontains=query)
            ).select_related('userProfile').order_by('-created_at')[:30]

            context['profiles'] = Profile.objects.filter(
                Q(user__username__icontains=query) | Q(bio__icontains=query)
            ).select_related('user').order_by('-created_at')[:20]

        return context

class PostsListView(ListView):
    model = Post
    template_name = 'posts/index.html'
    context_object_name = 'posts'


class PostCreateView(CreateView):
    model = Post
    fields = ['title', 'body', 'images']
    template_name = 'posts/post-create.html'

    def dispatch(self, request, *args, **kwargs):
        self.userProfile = get_object_or_404(Profile, user__username=kwargs['username'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.userProfile = self.userProfile

        response = super().form_valid(form)

        hashtags_str = self.request.POST.get('hashtags_input', '')
        if hashtags_str:
            tag_list = [t.strip().strip('#').lower() for t in hashtags_str.split(',') if t.strip()]
            for tag_name in tag_list:
                tag, created = Hashtag.objects.get_or_create(name=tag_name)
                self.object.hashtags.add(tag)

        return response

    def get_success_url(self):
        return reverse('profile_detail', kwargs={'username': self.userProfile.user.username})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.userProfile
        return context