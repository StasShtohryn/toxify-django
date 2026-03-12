import re
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, TemplateView, DetailView
from django.views import View
from django.db.models import Q
from django.contrib import messages

from . import forms
from .forms import ReportForm, PostsForm
from .models import Post, Hashtag, Comment, PostLike, Report, Reaction, CommentReaction, CommentLike
from .models import Post, Hashtag, Comment, Notification
from profiles.models import Profile, User, Repost


# Create your views here.


def _get_mentioned_usernames(text):
    """Повертає множину username з тексту (@username)."""
    if not text:
        return set()
    return set(re.findall(r'@(\w+)', text))


def _create_mention_notifications(sender, body, post, context_type):
    """Створює сповіщення для всіх згаданих через @ користувачів."""
    usernames = _get_mentioned_usernames(body)
    for username in usernames:
        try:
            recipient = User.objects.get(username__iexact=username)
        except User.DoesNotExist:
            continue
        if recipient == sender:
            continue
        title_preview = (post.title[:20] + '...') if post and post.title else 'post'
        if context_type == 'post':
            msg = f"mentioned you in a post: '{title_preview}'"
        else:
            msg = f"mentioned you in a comment on '{title_preview}'"
        Notification.objects.create(
            recipient=recipient,
            sender=sender,
            post=post,
            message=msg,
        )


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
    """Додає post.user_has_liked та post.user_has_reposted для кожного поста."""
    post_list = list(posts) if hasattr(posts, '__iter__') and not isinstance(posts, (str, dict)) else [posts]
    if not post_list:
        return
    post_ids = [p.id for p in post_list]
    if request.user.is_authenticated:
        liked_ids = set(PostLike.objects.filter(
            profile=request.user.profile,
            post_id__in=post_ids
        ).values_list('post_id', flat=True))
        reposted_ids = set(Repost.objects.filter(
            profile=request.user.profile,
            post_id__in=post_ids
        ).values_list('post_id', flat=True))
        for post in post_list:
            post.user_has_liked = post.id in liked_ids
            post.user_has_reposted = post.id in reposted_ids
    else:
        for post in post_list:
            post.user_has_liked = False
            post.user_has_reposted = False


class PostsListView(ListView):
    model = Post
    template_name = 'posts/index.html'
    context_object_name = 'posts'
    ordering = ['-created_at']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_detail'] = False
        user = self.request.user

        posts = context['posts']
        _add_liked_to_posts(self.request, posts)
        if user.is_authenticated:
            profile = user.profile
            for post in posts:
                last_comment = post.get_last_main_comment()
                if last_comment:
                    last_comment.user_has_liked = last_comment.comment_likes.filter(profile=profile).exists()
                    post.cached_last_comment = last_comment
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
        user = self.request.user

        _add_liked_to_posts(self.request, [context['post']])
        comments = list(
            context['post'].post_comments.all().prefetch_related('comment_likes', 'replies')
        )
        if user.is_authenticated:
            profile = user.profile
            # Отримуємо всі коментарі цього поста

            for comment in comments:
                comment.user_has_liked = comment.comment_likes.filter(profile=profile).exists()
                for reply in comment.replies.all():
                    reply.user_has_liked = reply.comment_likes.filter(profile=profile).exists()

        else:
            for comment in comments:
                comment.user_has_liked = False
                for reply in comment.replies.all():
                    reply.user_has_liked = False


        context['comments'] = comments

        referer = self.request.META.get('HTTP_REFERER')
        home_url = reverse('posts')

        if referer and self.request.get_host() in referer:
            current_path = self.request.path
            forbidden_words = ['like', 'react', 'comment', 'delete', 'edit']
            if any(word in referer for word in forbidden_words) or current_path in referer:
                context['back_url'] = home_url
            else:
                context['back_url'] = referer
        else:
            context['back_url'] = home_url

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
            form.instance.images = upload_to_vercel_blob(image_file, folder="posts")

        response = super().form_valid(form)

        hashtags_str = self.request.POST.get('hashtags_input', '')
        if hashtags_str:
            tag_list = [t.strip().strip('#').lower() for t in hashtags_str.split(',') if t.strip()]
            for tag_name in tag_list:
                tag, created = Hashtag.objects.get_or_create(name=tag_name)
                self.object.hashtags.add(tag)

        _create_mention_notifications(
            sender=self.request.user,
            body=self.object.body or '',
            post=self.object,
            context_type='post',
        )

        messages.success(self.request, "Post created successfully!")

        return response

    def get_success_url(self):
        return reverse('post_detail', kwargs={'post_id': self.object.pk}) + '?new=true'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.userProfile
        return context


class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Post
    template_name = 'posts/post_confirm_delete.html'
    success_url = reverse_lazy('posts')

    def test_func(self):
        post = self.get_object()
        return self.request.user == post.userProfile.user or self.request.user.is_superuser


class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    fields = ['title', 'body', 'images']
    template_name = 'posts/comment-create.html'

    def dispatch(self, request, *args, **kwargs):
        self.commentProfile = get_object_or_404(Profile, user__username=kwargs['username'])
        self.post_obj = get_object_or_404(Post, pk=kwargs['post_id'])
        return super().dispatch(request, *args, **kwargs)

    def create_comment_notification(self):
        new_comment = self.object
        sender = self.request.user

        # 1) Це відповідь на чийсь коментар (Reply)
        if new_comment.parent:
            recipient = new_comment.parent.commentProfile.user
            msg = f"replied to your comment on '{self.post_obj.title[:20]}...'"

        # 2) Це новий коментар до поста
        else:
            recipient = self.post_obj.userProfile.user
            msg = f"commented on your post: '{self.post_obj.title[:20]}...'"

        if recipient != sender:
            Notification.objects.create(
                recipient=recipient,
                sender=sender,
                post=self.post_obj,
                message=msg
            )

        _create_mention_notifications(
            sender=sender,
            body=new_comment.body or '',
            post=self.post_obj,
            context_type='comment',
        )

    def form_valid(self, form):
        form.instance.commentProfile = self.commentProfile
        form.instance.post_to = self.post_obj

        parent_id = self.request.POST.get('parent_id')
        if parent_id:
            form.instance.parent = Comment.objects.get(id=parent_id)

        image_file = self.request.FILES.get('images')
        if image_file:
            from utils.blobs import upload_to_vercel_blob
            form.instance.images = upload_to_vercel_blob(image_file, folder="comments")


        response = super().form_valid(form)
        self.create_comment_notification()

        return response

    def get_success_url(self):
        return reverse('post_detail', kwargs={'post_id': self.object.post_to.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.commentProfile
        return context



MAX_REPORTS = 2
@login_required
def report_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    author_profile = post.userProfile
    post_author = author_profile.user  # Якщо видалиться пост, треба знати автора

    if request.user == post_author:
        messages.warning(request, "You can't report your own post. That's just weird.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    if Report.objects.filter(reporter=request.user, post=post).exists():
        messages.warning(request, "You have already reported this post.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.post = post
            report.save()

            author_profile.reputation_score -= 20
            author_profile.recalculate_toxicity()
            author_profile.save()

            report_count = Report.objects.filter(post=post).count()
            reason_text = report.reason if report.reason else "No specific reason provided."


            Notification.objects.create(
                recipient=post_author,
                sender=request.user,
                post=post,
                message=f"reported your toxic post: '{post.title[:20]}...'\nReason:{reason_text}"
            )

            if report_count >= MAX_REPORTS:
                deleted_post_title = post.title[:20]
                post.delete()

                Notification.objects.create(
                    recipient=post_author,
                    sender=None,
                    post=None,
                    message=f"Your post '{deleted_post_title}' was deleted due to big amount of community reports!"
                )
                messages.info(request, "THANK YOU FOR BUILDING OUR APP BETTER! Post removed by community safety system.")
                return redirect(request.META.get('HTTP_REFERER', '/'))

            messages.success(request, f"Report recorded. ({report_count}/{MAX_REPORTS})")
            return redirect(request.META.get('HTTP_REFERER', '/'))

    return redirect(request.META.get('HTTP_REFERER', '/'))



MAX_COMMENT_REPORTS = 3
@login_required
def report_comment(request, comment_id):
    reporter = request.user
    comment = get_object_or_404(Comment, id=comment_id)
    comment_author_profile = comment.commentProfile
    comment_author = comment_author_profile.user

    if request.user == comment_author:
        messages.warning(request, "Reporting yourself? That's next-level toxicity.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    if Report.objects.filter(reporter=request.user, comment=comment).exists():
        messages.warning(request, "You already reported this comment.")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    if request.method == 'POST':
        reason_text = request.POST.get('reason', 'No specific reason provided.')

        Report.objects.create(
            reporter=request.user,
            comment=comment,
            reason=reason_text
        )

        comment_author_profile.reputation_score -= 3
        comment_author_profile.recalculate_toxicity()
        comment_author_profile.save()

        report_count = Report.objects.filter(comment=comment).count()

        comment_body_preview = comment.body[:20]
        if report_count >= MAX_COMMENT_REPORTS:
            comment.delete()

            Notification.objects.create(
                recipient=comment_author,
                sender=None,
                post=None,
                message=f"Your comment '{comment_body_preview}' was removed due to community reports."
            )
            messages.info(request, "THANK YOU FOR BUILDING OUR APP BETTER! Toxic comment was removed.")
        else:
            Notification.objects.create(
                recipient=comment_author,
                sender=reporter,
                post=None,
                message=f" report your comment '{comment_body_preview}...'\nReason:{reason_text}"
            )
            messages.success(request, f"Comment report recorded ({report_count}/{MAX_COMMENT_REPORTS}).")

    return redirect(request.META.get('HTTP_REFERER', '/'))



@login_required
def notifications_list(request):
    # 1. Отримуємо сповіщення
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    # Створюємо список непрочитаних ID, щоб передати їх у шаблон окремо,
    # або просто завантажуємо QuerySet у пам'ять через list()
    notifications_list = list(notifications)

    # 2. Оновлюємо статус у базі (це не вплине на вже завантажений notifications_list)
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)

    return render(request, 'posts/notifications.html', {'notifications': notifications_list})




class LikePostToggleView(LoginRequiredMixin, View):
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
            if post.userProfile != profile:
                Notification.objects.create(
                    recipient=post.userProfile.user,
                    sender=request.user,
                    post=post,
                    message=f"liked your toxic post: '{post.title[:20]}...'"
                )

        # Якщо запит асинхронний — повертаємо JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'liked': liked,
                'count': post.post_likes.count()
            })

        # Якщо синхронний — звичайний redirect
        redirect_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('posts')
        return redirect(redirect_url)



class LikeCommentToggleView(LoginRequiredMixin, View):
    login_url = '/profile/login/'

    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, pk=comment_id)
        profile = request.user.profile

        like, created = CommentLike.objects.get_or_create(profile=profile, comment=comment)
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
            author_profile = comment.commentProfile
            if author_profile != profile:
                Notification.objects.create(
                    recipient=author_profile.user,
                    sender=request.user,
                    post=comment.post_to,
                    message=f"liked your toxic comment: '{comment.body[:20]}...'"
                )

        return JsonResponse({
            'liked': liked,
            'count': comment.comment_likes.count()
        })


@login_required
def toggle_reaction(request, post_id, reaction_type):
    post = get_object_or_404(Post, id=post_id)
    author_profile = post.userProfile
    user = request.user

    if post.userProfile.user == request.user:
        messages.warning(request, "Self-praise is no praise. You can't rate your own post!")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    REACTION_WEIGHTS = {
        'based': 4,
        'toxic': -2,
        'cringe': -5,
    }

    existing_reaction = Reaction.objects.filter(user=user, post=post).first()
    send_notification = True

    if existing_reaction:
        # 1) Юзер натиснув на ту саму кнопку (хоче прибрати реакцію)
        if existing_reaction.type == reaction_type:
            author_profile.reputation_score -= REACTION_WEIGHTS[reaction_type]
            existing_reaction.delete()
            send_notification = False

        # 2) Юзер передумав і змінив тип (наприклад з Cringe на Based)
        else:
            author_profile.reputation_score -= REACTION_WEIGHTS[existing_reaction.type]
            author_profile.reputation_score += REACTION_WEIGHTS[reaction_type]
            existing_reaction.type = reaction_type
            existing_reaction.save()
            send_notification = True

    else:
        # 3) Юзер ставить реакцію вперше
        existing_reaction = Reaction.objects.create(user=user, post=post, type=reaction_type)
        author_profile.reputation_score += REACTION_WEIGHTS[reaction_type]

    author_profile.recalculate_toxicity()
    author_profile.save()

    if send_notification:
        Notification.objects.create(
            recipient = author_profile.user,
            sender=user,
            post=post,
            message=f" mark your post '{post.title}...' as {reaction_type.upper()}"
        )

    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def toggle_comment_reaction(request, comment_id, reaction_type):
    comment = get_object_or_404(Comment, id=comment_id)
    author_profile = comment.commentProfile
    user = request.user

    if author_profile.user == user:
        messages.warning(request, "You can't rate your own comment!")
        return redirect(request.META.get('HTTP_REFERER', '/'))

    REACTION_WEIGHTS = {
        'based': 4,
        'toxic': -2,
        'cringe': -5
    }

    existing_reaction = CommentReaction.objects.filter(user=user, comment=comment).first()
    send_notification = True

    if existing_reaction:
        if existing_reaction.type == reaction_type:
            author_profile.reputation_score -= REACTION_WEIGHTS[reaction_type]
            existing_reaction.delete()
            send_notification = False
        else:
            author_profile.reputation_score -= REACTION_WEIGHTS[existing_reaction.type]
            author_profile.reputation_score += REACTION_WEIGHTS[reaction_type]
            existing_reaction.type = reaction_type
            existing_reaction.save()
    else:
        CommentReaction.objects.create(user=user, comment=comment, type=reaction_type)
        author_profile.reputation_score += REACTION_WEIGHTS[reaction_type]

    author_profile.recalculate_toxicity()
    author_profile.save()

    if send_notification:
        Notification.objects.create(
            recipient=author_profile.user,
            sender=user,
            post=comment.post_to,
            message=f"marked your comment as {reaction_type.upper()}"
        )

    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    post_id = comment.post_to.id
    if comment.commentProfile.user == request.user:
        comment.delete()
    return redirect('post_detail', post_id=post_id)


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.userProfile.user != request.user:
        return redirect('post_list')

    if request.method == "POST":
        # Передаємо інстанс, щоб Django знав, який пост оновлювати
        form = PostsForm(request.POST, request.FILES, instance=post)

        if form.is_valid():
            updated_post = form.save(commit=False)

            if 'images' in request.FILES:
                updated_post.image = request.FILES['images']

            updated_post.save()

            hashtags_input = request.POST.get('hashtags_input', '')
            if hashtags_input:
                updated_post.hashtags.clear()
                for tag_name in hashtags_input.split(','):
                    tag_name = tag_name.strip().lower()
                    if tag_name:
                        from .models import Tag
                        tag, created = Tag.objects.get_or_create(name=tag_name)
                        updated_post.hashtags.add(tag)

            return redirect('post_detail', post_id=updated_post.id)
    else:
        form = PostsForm(instance=post)
        current_tags = ", ".join([tag.name for tag in post.hashtags.all()])

    return render(request, 'posts/post-edit.html', {
        'form': form,
        'post': post,
        'current_tags': current_tags
    })