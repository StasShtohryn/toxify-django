from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from .models import Notification, Post


