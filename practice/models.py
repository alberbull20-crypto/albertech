from django.db import models
from django.contrib.auth.models import User


class Challenge(models.Model):
    DIFFICULTY_CHOICES = [
        ("easy", "Easy"),
        ("medium", "Medium"),
        ("hard", "Hard"),
    ]

    title = models.CharField(max_length=200)
    prompt = models.TextField(help_text="Explain what the student needs to do or figure out.")
    code_snippet = models.TextField(blank=True, help_text="Code shown to the student, if any.")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default="easy")
    expected_answer = models.CharField(max_length=300, help_text="Exact expected answer (matched case-insensitively, trimmed).")
    explanation = models.TextField(help_text="Shown after submission, right or wrong.")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class ChallengeCompletion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="challenge_completions")
    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name="completions")
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "challenge")