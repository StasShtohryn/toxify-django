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

def user_directory_path(instance, filename):
    return f'user_{instance.profile.id}/photo_posts/%Y/%M/%D/{filename}'

class Post(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='posts')
    title = models.CharField(max_length=100)
    body = models.TextField(null=True, blank=True)
    # hashtags = ArrayField(models.CharField(max_length=100), blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    images = models.ImageField(upload_to=user_directory_path, null=True, blank=True,
            validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp']),
            validate_size])




