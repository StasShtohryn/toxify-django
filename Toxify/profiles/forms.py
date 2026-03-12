from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import User, Profile

class LoginForm(AuthenticationForm):
    error_messages = {
        'invalid_login': 'Invalid username or password.',
        'inactive': 'This account is inactive.',
    }

class RegisterForm(UserCreationForm):

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
            profile, created = Profile.objects.get_or_create(user=user)
            profile.name = self.cleaned_data['name']
            profile.save()
        return user


class ProfileEditForm(forms.ModelForm):

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


class UsernameEditForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ("username", "email")