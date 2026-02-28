import os

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from .models import Profile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Сигнал: новий User → автоматично створити Profile."""
    if created:
        Profile.objects.get_or_create(user=instance)


def delete_file(file_field) -> None:
    if file_field and os.path.isfile(file_field.path):
        os.remove(file_field.path)


@receiver(pre_delete, sender=Profile)
def delete_avatar_on_profile_delete(sender, instance, **kwargs):
    """
    Спрацьовує ПЕРЕД видаленням профілю (разом з акаунтом).
    Видаляє аватар з диску.
    """
    delete_file(instance.avatar)


@receiver(pre_save, sender=Profile)
def delete_old_avatar_on_update(sender, instance, **kwargs):
    """
    Спрацьовує ПЕРЕД збереженням профілю.
    Якщо юзер змінив аватар — видаляє старий файл з диску.
    """
    # Новий профіль — нема чого видаляти
    if not instance.pk:
        return

    try:
        old_avatar = Profile.objects.get(pk=instance.pk).avatar
    except Profile.DoesNotExist:
        return

    new_avatar = instance.avatar

    # Якщо аватар змінився і старий файл існує — видаляємо
    if old_avatar and old_avatar != new_avatar:
        delete_file(old_avatar)