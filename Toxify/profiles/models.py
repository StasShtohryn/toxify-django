from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Count
from utils.blobs import url


class User(AbstractUser):
    pass


class Profile(models.Model):
    """
    User profile. One-to-one relation with User.
    Contains: avatar, bio, toxicity level, subscriptions, post statistics.
    """

    # ── Basic fields ─────────────────────────────────────────────────────────
    name = models.CharField(max_length=50)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    avatar = models.URLField(
        blank=True,
        default=f'{url}avatars/default.jpg',
        null=True,
        help_text="Profile picture",
    )

    bio = models.TextField(
        max_length=300,
        blank=True,
        default="",
        help_text="Tell something about yourself (or don't — this is Toxify)",
    )

    tag = models.CharField(
        max_length=30,
        blank=True,
        default='',
    )

    # Private profile: content visible only to followers
    is_closed = models.BooleanField(
        default=False,
        help_text="If True — posts/reposts/replies are visible only to followers",
    )

    # ── Subscriptions ────────────────────────────────────────────────────────
    following = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="followers",
        help_text="Users that this profile follows",
    )

    # ── Toxicity system ──────────────────────────────────────────────────────
    TOXICITY_CHOICES = [
        (0, "😇 Innocent"),
        (1, "😐 Edgy"),
        (2, "😤 Salty"),
        (3, "🤬 Toxic"),
        (4, "☢️ Radioactive"),
        (5, "💀 Banned-worthy"),
    ]

    toxicity_level = models.PositiveSmallIntegerField(
        choices=TOXICITY_CHOICES,
        default=0,
        help_text="Automatically updated based on reports",
    )

    reputation_score = models.IntegerField(
        default=0,
        help_text="Positive = likes, negative = reports. Can go below zero.",
    )

    # ── Metadata ─────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Profile"
        verbose_name_plural = "Profiles"

    def __str__(self):
        return f"@{self.user.username} [{self.get_toxicity_level_display()}]"

    # ── Properties ───────────────────────────────────────────────────────────

    @property
    def followers_count(self) -> int:
        return self.followers.count()

    @property
    def following_count(self) -> int:
        return self.following.count()

    @property
    def posts_count(self) -> int:
        # Assumes Post has ForeignKey(User, related_name='posts')
        return self.user.posts.count()

    @property
    def has_unread_notifications(self):
        return self.user.notifications.filter(is_read=False).exists()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def is_following(self, other_profile: "Profile") -> bool:
        """Checks if the current profile follows another profile."""
        return self.following.filter(pk=other_profile.pk).exists()

    def recalculate_toxicity(self) -> None:
        """
        Recalculates toxicity level based on reputation_score.
        Should be called after each report or like.
        """
        score = self.reputation_score

        if score >= 50:
            level = 0
        elif score >= 10:
            level = 1
        elif score >= 0:
            level = 2
        elif score >= -20:
            level = 3
        elif score >= -50:
            level = 4
        else:
            level = 5

        self.toxicity_level = level
        self.save(update_fields=["toxicity_level"])


class Repost(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="reposts",
    )

    post = models.ForeignKey(
        "posts.Post",
        on_delete=models.CASCADE,
        related_name="reposted_by",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("profile", "post")