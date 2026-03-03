from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, TemplateView, DetailView
from django.views import View
from django.db.models import Q

from . import forms
from .models import Post, Hashtag, Comment, PostLike
from profiles.models import Profile, User


# Create your views here.

class SearchView(TemplateView):
    template_name = 'posts/search.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '').strip()
        context['query'] = query

        if not query:
            return context

        if query.startswith('#'):
            tag_name = query.lstrip('#').lower()
            context['posts'] = Post.objects.filter(
                hashtags__name__icontains=tag_name
            ).select_related('userProfile__user').distinct().order_by('-created_at')[:30]
            _add_liked_to_posts(self.request, context['posts'])
            context['search_type'] = 'hashtag'

        elif query.startswith('@'):
            username = query.lstrip('@')
            context['profiles'] = Profile.objects.filter(
                user__username__icontains=username
            ).select_related('user').order_by('-created_at')[:20]
            context['search_type'] = 'mention'

        else:
            context['posts'] = Post.objects.filter(
                Q(title__icontains=query) | Q(body__icontains=query) | Q(hashtags__name__icontains=query)
            ).select_related('userProfile__user').distinct().order_by('-created_at')[:30]
            _add_liked_to_posts(self.request, context['posts'])

            context['profiles'] = Profile.objects.filter(
                Q(user__username__icontains=query) | Q(bio__icontains=query)
            ).select_related('user').order_by('-created_at')[:20]

        return context

def _add_liked_to_posts(request, posts):
    """Додає post.user_has_liked для кожного поста."""
    post_list = list(posts) if hasattr(posts, '__iter__') and not isinstance(posts, (str, dict)) else [posts]
    if not post_list:
        return
    if request.user.is_authenticated:
        liked_ids = set(PostLike.objects.filter(
            profile=request.user.profile,
            post_id__in=[p.id for p in post_list]
        ).values_list('post_id', flat=True))
        for post in post_list:
            post.user_has_liked = post.id in liked_ids
    else:
        for post in post_list:
            post.user_has_liked = False


class PostsListView(ListView):
    model = Post
    template_name = 'posts/index.html'
    context_object_name = 'posts'
    ordering = ['-created_at']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_detail'] = False
        posts = list(context.get('posts', []))
        _add_liked_to_posts(self.request, posts)
        context['posts'] = posts
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'posts/post-detail.html'
    context_object_name = 'post'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_detail'] = True
        _add_liked_to_posts(self.request, [context['post']])

        # Отримуємо URL, з якого прийшов користувач
        referer = self.request.META.get('HTTP_REFERER')

        # Якщо реферер є і він веде на наш сайт (а не на Google, наприклад), передаємо його
        if referer and self.request.get_host() in referer:
            context['back_url'] = referer
        else:
            context['back_url'] = reverse('posts')  # Дефолт на головну

        return context


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    fields = ['title', 'body', 'images']
    template_name = 'posts/post-create.html'


    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Змінюємо кількість рядків (rows) та додаємо класи Tailwind
        form.fields['body'].widget.attrs.update({
            'rows': '2',
        })
        return form

    def dispatch(self, request, *args, **kwargs):
        self.userProfile = get_object_or_404(Profile, user__username=kwargs['username'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.userProfile = self.userProfile
        image_file = self.request.FILES.get('images')
        if image_file:
            from utils.blobs import upload_to_vercel_blob
            form.instance.images = upload_to_vercel_blob(image_file)

        response = super().form_valid(form)

        hashtags_str = self.request.POST.get('hashtags_input', '')
        if hashtags_str:
            tag_list = [t.strip().strip('#').lower() for t in hashtags_str.split(',') if t.strip()]
            for tag_name in tag_list:
                tag, created = Hashtag.objects.get_or_create(name=tag_name)
                self.object.hashtags.add(tag)

        return response

    def get_success_url(self):
        return reverse('post_detail', kwargs={'post_id': self.object.pk}) + '?new=true'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.userProfile
        return context




class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ['title', 'body', 'images']
    template_name = 'posts/comment-create.html'

    def dispatch(self, request, *args, **kwargs):
        self.commentProfile = get_object_or_404(Profile, user__username=kwargs['username'])
        self.post_obj = get_object_or_404(Post, pk=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.commentProfile = self.commentProfile
        form.instance.post_to = self.post_obj

        parent_id = self.request.POST.get('parent_id')
        if parent_id:
            form.instance.parent = Comment.objects.get(id=parent_id)

        image_file = self.request.FILES.get('images')
        if image_file:
            from utils.blobs import upload_to_vercel_blob
            form.instance.images = upload_to_vercel_blob(image_file)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('post_detail', kwargs={'post_id': self.object.post_to.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.commentProfile
        return context


@login_required
def report_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    author_profile = post.userProfile

    author_profile.reputation_score -= 1

    rep = author_profile.reputation_score
    if rep >= 50:
        author_profile.toxicity_level = 0
    elif rep >= 10:
        author_profile.toxicity_level = 1
    elif rep >= 0:
        author_profile.toxicity_level = 2
    elif rep >= -20:
        author_profile.toxicity_level = 3
    elif rep >= -50:
        author_profile.toxicity_level = 4
    else:
        author_profile.toxicity_level = 5
    author_profile.save()

    return redirect(request.META.get('HTTP_REFERER', '/'))


class LikePostToggleView(LoginRequiredMixin, View):
    """POST: поставити або зняти лайк з поста."""
    login_url = '/profile/login/'

    def post(self, request, post_id):
        post = get_object_or_404(Post, pk=post_id)
        profile = request.user.profile

        like, created = PostLike.objects.get_or_create(profile=profile, post=post)
        if not created:
            like.delete()
            liked = False
        else:
            liked = True

        redirect_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('posts')
        return redirect(redirect_url)