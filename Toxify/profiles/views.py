from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import DetailView, FormView

from posts.models import Post, Report, Notification, Comment
from posts.views import _add_liked_to_posts
from .forms import ProfileEditForm, RegisterForm, UsernameEditForm
from .models import User, Profile, Repost
from utils.blobs import upload_to_vercel_blob

# ── Реєстрація ────────────────────────────────────────────────────────────────

class RegisterView(FormView):
    """
    GET  → рендерить форму реєстрації
    POST → створює User + UserProfile, логінить, редіректить на профіль
    """
    template_name = "profiles/register.html"
    form_class = RegisterForm

    def dispatch(self, request, *args, **kwargs):
        # Якщо вже залогінений — одразу на профіль
        if request.user.is_authenticated:
            return redirect("profile_detail", username=request.user.username)
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, f"Welcome to Toxify, @{user.username}! 🤬")
        return redirect("profile_detail", username=user.username)


# ── Публічний профіль ─────────────────────────────────────────────────────────

class ProfileDetailView(DetailView):
    """
    Публічна сторінка профілю будь-якого юзера.
    URL: /users/<username>/
    """
    model = Profile
    template_name = "profiles/profile_detail.html"
    context_object_name = "profile"

    def get_object(self, queryset=None):
        return get_object_or_404(
            Profile,
            user__username=self.kwargs["username"],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.get_object()

        context["is_owner"] = self.request.user == profile.user
        context["is_following"] = (
            self.request.user.is_authenticated
            and self.request.user != profile.user
            and self.request.user.profile.is_following(profile)
        )

        # Закритий профіль: контент бачать тільки власник або підписники
        can_see_content = context["is_owner"] or (
            profile.is_closed and context["is_following"]
        ) or not profile.is_closed
        context["profile_is_hidden"] = not can_see_content

        if can_see_content:
            posts = list(profile.posts.order_by("-created_at")[:20])
            _add_liked_to_posts(self.request, posts)
            context["posts"] = posts

            reposts_qs = Repost.objects.filter(profile=profile).select_related('post', 'post__userProfile', 'post__userProfile__user').order_by('-created_at')[:20]
            reposted_posts = [r.post for r in reposts_qs]
            _add_liked_to_posts(self.request, reposted_posts)
            context["reposted_posts"] = reposted_posts

            context['replies'] = Comment.objects.filter(
                commentProfile=profile
            ).select_related('post_to').order_by('-created_at')
        else:
            context["posts"] = []
            context["reposted_posts"] = []
            context["replies"] = []

        return context


# ── Редагування профілю ───────────────────────────────────────────────────────

class ProfileEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    """
    Дві форми на одній сторінці:
      - ProfileEditForm  → зберігає avatar + bio (модель UserProfile)
      - UsernameEditForm → зберігає username + email (модель User)

    Розрізняються по імені submit-кнопки в POST: save_profile / save_account
    """
    template_name = "profiles/profile_edit.html"
    login_url = reverse_lazy("login")

    def test_func(self):
        # Тільки власник може редагувати свій профіль
        return self.request.user.is_authenticated

    def _render(self, request, profile_form, account_form):
        return render(request, self.template_name, {
            "profile_form": profile_form,
            "account_form": account_form,
            "profile": request.user.profile,
        })

    def get(self, request, *args, **kwargs):
        return self._render(
            request,
            ProfileEditForm(instance=request.user.profile),
            UsernameEditForm(instance=request.user),
        )

    def post(self, request, *args, **kwargs):
        if "save_profile" in request.POST:
            form = ProfileEditForm(
                request.POST, request.FILES, instance=request.user.profile
            )
            print("save_profile 1")
            if form.is_valid():
                print("save_profile 2")
                profile = form.save(commit=False)
                avatar_file = request.FILES.get('avatar')
                if avatar_file:
                    profile.avatar = upload_to_vercel_blob(avatar_file, folder="avatars")

                profile.save()
                messages.success(request, "Profile updated!")
                return redirect("profile_detail", username=request.user.username)
            return self._render(request, form, UsernameEditForm(instance=request.user))

        elif "save_account" in request.POST:
            form = UsernameEditForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "Account updated!")
                return redirect("profile_detail", username=request.user.username)
            return self._render(request, ProfileEditForm(instance=request.user.profile), form)

        return redirect("profile_detail", username=request.user.username)


# ── Follow / Unfollow ─────────────────────────────────────────────────────────

class FollowToggleView(LoginRequiredMixin, View):
    """
    POST /users/<username>/follow/
    Підтримує звичайний POST (редірект) та AJAX (JSON-відповідь).
    """
    login_url = reverse_lazy("login")

    def post(self, request, username: str):
        target_user = get_object_or_404(User, username=username)

        if target_user == request.user:
            if self._is_ajax(request):
                return JsonResponse(
                    {"error": "You can't subscribe yourself!"}, status=400
                )
            messages.errors(request, "You can't subscribe yourself!")
            return redirect("profile_detail", username=username)

        my_profile = request.user.profile
        target_profile = target_user.profile

        if my_profile.is_following(target_profile):
            my_profile.following.remove(target_profile)
            following = False
        else:
            my_profile.following.add(target_profile)
            following = True

            Notification.objects.create(
                recipient=target_user,
                sender=request.user,
                post=None,
                message=f" started following you!"
            )

        if self._is_ajax(request):
            return JsonResponse({
                "following": following,
                "followers_count": target_profile.followers_count,
            })

        return redirect("profile_detail", username=username)

    @staticmethod
    def _is_ajax(request) -> bool:
        return request.headers.get("x-requested-with") == "XMLHttpRequest"



class RepostToggleView(LoginRequiredMixin, View):
    """
    POST /posts/<pk>/repost/
    Якщо юзер ще не репостив — створює Repost.
    Якщо вже репостив — видаляє.
    Підтримує звичайний POST (редірект) та AJAX (JSON).
    """
    login_url = reverse_lazy("login")

    def post(self, request, pk: int):
        post = get_object_or_404(Post, pk=pk)

        # Не можна репостити власний пост
        if post.userProfile == request.user.profile:
            if self._is_ajax(request):
                return JsonResponse(
                    {"error": "Не можна репостити власний пост."}, status=400
                )
            return redirect("post_detail", post_id=pk)

        repost, created = Repost.objects.get_or_create(
            profile=request.user.profile,
            post=post,
        )

        if not created:
            # Вже репостив — видаляємо
            repost.delete()
            reposted = False
        else:
            reposted = True

        if self._is_ajax(request):
            return JsonResponse({
                "reposted": reposted,
                "reposts_count": post.reposted_by.count(),
            })

        next_url = request.POST.get("next") or request.META.get("HTTP_REFERER")
        if next_url:
            return redirect(next_url)
        return redirect("post_detail", post_id=pk)

    @staticmethod
    def _is_ajax(request) -> bool:
        return request.headers.get("x-requested-with") == "XMLHttpRequest"


@login_required
def user_search_api(request):
    """API для пошуку користувачів по @ згадках."""
    q = request.GET.get("q", "").strip()
    if not q:
        return JsonResponse({"users": []})
    profiles = Profile.objects.filter(
        Q(user__username__icontains=q) | Q(name__icontains=q)
    ).select_related("user").order_by("user__username")[:10]
    return JsonResponse({
        "users": [
            {
                "username": p.user.username,
                "name": p.name or p.user.username,
                "avatar": p.avatar or "",
                "url": reverse("profile_detail", args=[p.user.username]),
            }
            for p in profiles
        ]
    })