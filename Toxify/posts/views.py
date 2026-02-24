from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView

from posts.models import Post
from profiles.models import Profile


# Create your views here.

class PostsListView(ListView):
    model = Post
    template_name = 'posts/posts.html'
    context_object_name = 'posts'


class PostCreateView(CreateView):
    model = Post
    fields = ['title', 'body', 'image']
    template_name = 'posts/post-create.html'

    def dispatch(self, request, *args, **kwargs):
        self.profile = get_object_or_404(Profile, pk=kwargs['profile_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.profile = self.profile
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('profile_detail', kwargs={'pk': self.profile.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.profile
        return context