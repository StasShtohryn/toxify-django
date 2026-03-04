from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

SIZE = (1200, 1200)


def validate_size(fieldfile_obj):
    size_limit = 75.0
    if fieldfile_obj.size > size_limit * 1024 * 1024:
        raise ValidationError(f"Файл занадто великий! Максимум {size_limit} MB")

def user_directory_post_path(instance, filename):
    return f'user_{instance.userProfile.user.username}/photo_posts/%Y/%m/%D/{filename}'

def user_directory_comment_path(instance, filename):
    return f'user_{instance.commentProfile.user.username}/photo_comments/%Y/%m/%D/{filename}'



class Hashtag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"#{self.name}"


class Post(models.Model):
    userProfile = models.ForeignKey(
        "profiles.Profile",  # ← рядок замість імпорту
        on_delete=models.CASCADE,
        related_name='posts'
    )
    title = models.CharField(max_length=100)
    body = models.TextField(null=True, blank=True)
    hashtags = models.ManyToManyField(Hashtag, blank=True, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)
    images = models.URLField(max_length=500, null=True, blank=True)

    def get_last_main_comment(self):
        return self.post_comments.filter(parent__isnull=True).last()


class PostLike(models.Model):
    """Лайк поста. Один юзер — один лайк на пост."""
    profile = models.ForeignKey(
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name='post_likes'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='post_likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('profile', 'post')


class Comment(models.Model):
    commentProfile = models.ForeignKey(
        "profiles.Profile",  # ← рядок замість імпорту
        on_delete=models.CASCADE,
        related_name='comments'
    )
    post_to = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_comments')
    title = models.CharField(max_length=100)
    body = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Нескінченні коментарі, поле для посилання на самого себе
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )


    images = models.URLField(null=True, blank=True)


class Report(models.Model):
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_reports'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='reports'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Заборона на повторну скаргу
    class Meta:
        unique_together = ('reporter', 'post')

    def __str__(self):
        return f"{self.reporter} reported {self.post.title}"



class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null = True,
        blank = True,
    )
    post = models.ForeignKey('Post', on_delete=models.CASCADE, null = True,
        blank = True)
    message = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

