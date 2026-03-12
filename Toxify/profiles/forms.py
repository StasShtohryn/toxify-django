from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import User, Profile

class LoginForm(AuthenticationForm):
    error_messages = {
        'invalid_login': 'Невірний логін або пароль.',
        'inactive': 'Цей акаунт неактивний.',
    }

class RegisterForm(UserCreationForm):
    """Реєстрація: username + email + пароль."""

    name = forms.CharField(required=True, label='Name')
    email = forms.EmailField(required=True, label="Email")

    class Meta:
        model = User
        fields = ('name', "username", "email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            # Профіль створюється автоматично через сигнал (див. нижче),
            # але про всяк випадок — get_or_create
            profile, created = Profile.objects.get_or_create(user=user)
            profile.name = self.cleaned_data['name']
            profile.save()
        return user


class ProfileEditForm(forms.ModelForm):
    """Редагування профілю: аватар + біо + закритий профіль."""

    class Meta:
        model = Profile
        fields = ('name', "bio", 'tag', 'is_closed')
        labels = {
            'is_closed': 'Closed profile',
        }
        help_texts = {
            'is_closed': 'Only followers can see your posts and replies',
        }
        widgets = {
            'name': forms.TextInput(
                attrs={
                    'placeholder': 'Enter your name'
                }
            ),
            "bio": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Tell something toxic about yourself...",
                }
            ),
            'tag': forms.TextInput(
                attrs={
                    'placeholder': 'Your status...'
                }
            ),
            'is_closed': forms.CheckboxInput(attrs={'class': 'w-4 h-4 accent-green-500'}),
        }

    def clean_bio(self):
        bio = self.cleaned_data.get("bio", "")
        if len(bio) > 300:
            raise forms.ValidationError("Bio cannot exceed 300 characters.")
        return bio

    # def clean_avatar(self):
    #     avatar = self.cleaned_data.get("avatar")
    #     if avatar:
    #         # Максимум 2 МБ
    #         if avatar.size > 2 * 1024 * 1024:
    #             raise forms.ValidationError("Розмір аватара не може перевищувати 2 МБ.")
    #         allowed = ("image/jpeg", "image/png", "image/webp", "image/gif")
    #         if hasattr(avatar, "content_type") and avatar.content_type not in allowed:
    #             raise forms.ValidationError("Дозволені формати: JPEG, PNG, WebP, GIF.")
    #     return avatar


class UsernameEditForm(forms.ModelForm):
    """Окрема форма для зміни username."""

    class Meta:
        model = User
        fields = ("username", "email")