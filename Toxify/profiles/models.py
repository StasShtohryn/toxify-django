from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Count


class User(AbstractUser):
    pass


class Profile(models.Model):
    """
    Профіль користувача. Зв'язок 1-до-1 з User.
    Містить: аватар, біо, токсик-рівень, підписки, статистику постів.
    """

    # ── Базові поля ──────────────────────────────────────────────────────────
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        help_text="Фото профілю",
    )
    bio = models.TextField(
        max_length=300,
        blank=True,
        default="",
        help_text="Розкажи про себе (або не розказуй — це Toxify)",
    )

    # ── Підписки ─────────────────────────────────────────────────────────────
    following = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="followers",
        help_text="На кого підписаний цей юзер",
    )

    # ── Токсик-система ───────────────────────────────────────────────────────
    TOXICITY_CHOICES = [
        (0, "😇 Innocent"),
        (1, "😐 Edgy"),
        (2, "😤 Salty"),
        (3, "🤬 Toxic"),
        (4, "☢️  Radioactive"),
        (5, "💀 Banned-worthy"),
    ]
    toxicity_level = models.PositiveSmallIntegerField(
        choices=TOXICITY_CHOICES,
        default=0,
        help_text="Автоматично оновлюється на основі репортів",
    )
    reputation_score = models.IntegerField(
        default=0,
        help_text="Позитивне = лайки, негативне = репорти. Може йти в мінус.",
    )

    # ── Мета ─────────────────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Профіль"
        verbose_name_plural = "Профілі"

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
        # Припускається, що Post має ForeignKey(User, related_name='posts')
        return self.user.posts.count()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def is_following(self, other_profile: "Profile") -> bool:
        """Чи підписаний поточний профіль на other_profile."""
        return self.following.filter(pk=other_profile.pk).exists()

    def recalculate_toxicity(self) -> None:
        """
        Перераховує токсик-рівень на основі reputation_score.
        Викликати після кожного репорту / лайку.
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