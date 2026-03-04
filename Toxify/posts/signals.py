from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.shortcuts import get_object_or_404, redirect

from utils.blobs import delete_from_vercel_blob
from .models import Notification, Post


@receiver(pre_delete, sender='posts.Post')
def delete_post_image_on_delete(sender, instance, **kwargs):
    delete_from_vercel_blob(instance.images)


@receiver(pre_save, sender='posts.Post')
def delete_old_post_image_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return
    Post = apps.get_model('posts', 'Post')
    try:
        old_image = Post.objects.get(pk=instance.pk).images
    except Post.DoesNotExist:
        return
    if old_image and old_image != instance.images:
        delete_from_vercel_blob(old_image)


@receiver(pre_delete, sender='posts.Comment')
def delete_comment_image_on_delete(sender, instance, **kwargs):
    delete_from_vercel_blob(instance.images)


@receiver(pre_save, sender='posts.Comment')
def delete_old_comment_image_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return
    Comment = apps.get_model('posts', 'Comment')
    try:
        old_image = Comment.objects.get(pk=instance.pk).images
    except Comment.DoesNotExist:
        return
    if old_image and old_image != instance.images:
        delete_from_vercel_blob(old_image)