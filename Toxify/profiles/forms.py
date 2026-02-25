from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User, Profile


class RegisterForm(UserCreationForm):
    """Реєстрація: username + email + пароль."""

    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            # Профіль створюється автоматично через сигнал (див. нижче),
            # але про всяк випадок — get_or_create
            Profile.objects.get_or_create(user=user)
        return user


class ProfileEditForm(forms.ModelForm):
    """Редагування профілю: аватар + біо."""

    class Meta:
        model = Profile
        fields = ("avatar", "bio")
        widgets = {
            "bio": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Розкажи щось токсичне про себе...",
                }
            ),
        }

    def clean_bio(self):
        bio = self.cleaned_data.get("bio", "")
        if len(bio) > 300:
            raise forms.ValidationError("Біо не може перевищувати 300 символів.")
        return bio

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if avatar:
            # Максимум 2 МБ
            if avatar.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Розмір аватара не може перевищувати 2 МБ.")
            allowed = ("image/jpeg", "image/png", "image/webp", "image/gif")
            if hasattr(avatar, "content_type") and avatar.content_type not in allowed:
                raise forms.ValidationError("Дозволені формати: JPEG, PNG, WebP, GIF.")
        return avatar


class UsernameEditForm(forms.ModelForm):
    """Окрема форма для зміни username."""

    class Meta:
        model = User
        fields = ("username", "email")