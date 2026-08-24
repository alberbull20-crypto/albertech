from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    middle_name = models.CharField(max_length=100, blank=True)

    def full_name(self):
        parts = [self.user.first_name, self.middle_name, self.user.last_name]
        return " ".join(p for p in parts if p)

    def __str__(self):
        return self.full_name() or self.user.username