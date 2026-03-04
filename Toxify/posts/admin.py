from django.contrib import admin
from .models import Post, Comment, Hashtag, Notification, PostLike, Report

admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Hashtag)
admin.site.register(Notification)
admin.site.register(Report)
admin.site.register(PostLike)