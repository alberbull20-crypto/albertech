from django.contrib import admin
from .models import Challenge, ChallengeCompletion

admin.site.register(Challenge)
admin.site.register(ChallengeCompletion)