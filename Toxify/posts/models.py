from django.db import models
from profiles.models import Profile


# Create your models here.
class Post(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='posts')



