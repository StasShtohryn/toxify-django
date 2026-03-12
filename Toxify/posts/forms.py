from django import forms
from .models import Post, Report, Comment


class PostsForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'body', 'images']


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason']
        widgets = {
            'reason': forms.Textarea(attrs={
                'placeholder': 'Explain why this post is toxic...',
                'rows': 3,
                'class': 'w-full bg-black/40 border border-white/10 text-white p-2 text-sm focus:border-red-500 outline-none'
            }),
        }