from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import DetailView, FormView

from .forms import ProfileEditForm, RegisterForm, UsernameEditForm
from .models import User, Profile


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
        messages.success(self.request, f"Ласкаво просимо до Toxify, @{user.username}! 🤬")
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
        context["posts"] = profile.user.posts.order_by("-created_at")[:20]
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
            if form.is_valid():
                form.save()
                messages.success(request, "Профіль оновлено ✅")
                return redirect("profile_edit")
            return self._render(request, form, UsernameEditForm(instance=request.user))

        elif "save_account" in request.POST:
            form = UsernameEditForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "Акаунт оновлено ✅")
                return redirect("profile_edit")
            return self._render(request, ProfileEditForm(instance=request.user.profile), form)

        return redirect("profile_edit")


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
                    {"error": "Не можна підписатись на себе."}, status=400
                )
            return redirect("profile_detail", username=username)

        my_profile = request.user.profile
        target_profile = target_user.profile

        if my_profile.is_following(target_profile):
            my_profile.following.remove(target_profile)
            following = False
        else:
            my_profile.following.add(target_profile)
            following = True

        if self._is_ajax(request):
            return JsonResponse({
                "following": following,
                "followers_count": target_profile.followers_count,
            })

        return redirect("profile_detail", username=username)

    @staticmethod
    def _is_ajax(request) -> bool:
        return request.headers.get("x-requested-with") == "XMLHttpRequest"