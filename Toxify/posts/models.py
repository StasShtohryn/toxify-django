from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from profiles.models import Profile
# from django_better_admin_arrayfield.models.fields import ArrayField # Requires separate package for better admin widget

SIZE = (1200, 1200)


# Create your models here.

def validate_size(fieldfile_obj):
    size_limit = 75.0
    if fieldfile_obj.size > size_limit * 1024 * 1024:
        raise ValidationError(f"Файл занадто великий! Максимум {size_limit} MB")

def user_directory_post_path(instance, filename):
    return f'user_{instance.userProfile.user.username}/photo_posts/%Y/%m/%D/{filename}'

def user_directory_comment_path(instance, filename):
    return f'user_{instance.userProfile.user.username}/photo_comments/%Y/%m/%D/{filename}'

class Hashtag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"#{self.name}"

class Post(models.Model):
    userProfile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=100)
    body = models.TextField(null=True, blank=True)
    hashtags = models.ManyToManyField(Hashtag, blank=True, related_name='posts')
    created_at = models.DateTimeField(auto_now_add=True)

    images = models.ImageField(
            upload_to=user_directory_post_path,
            null=True,
            blank=True,
            validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp']),
            validate_size]
    )


class Comment(models.Model):
    commentProfile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='сomments')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    title = models.CharField(max_length=100)
    body = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    images = models.ImageField(
            upload_to=user_directory_comment_path,
            null=True,
            blank=True,
            validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp']),
            validate_size]
    )