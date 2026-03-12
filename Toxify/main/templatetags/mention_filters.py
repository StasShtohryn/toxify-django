import re
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.urls import reverse

register = template.Library()


@register.filter
def linkify_mentions(text):
    """
    Converts @username in text to clickable links to user profiles.
    """
    if not text:
        return ''
    text = escape(str(text))
    pattern = r'@(\w+)'

    def replace_mention(match):
        username = match.group(1)
        try:
            url = reverse('profile_detail', kwargs={'username': username})
            return f'<a href="{url}" class="text-green-400 hover:text-green-300 hover:underline font-medium">@{escape(username)}</a>'
        except Exception:
            return match.group(0)

    result = re.sub(pattern, replace_mention, text)
    return mark_safe(result)
