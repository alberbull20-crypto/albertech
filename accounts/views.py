from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView
from courses.models import Course
from .forms import SignUpForm, EmailAuthenticationForm, ProfileUpdateForm


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["student_count"] = User.objects.count()
        context["course_count"] = Course.objects.count()
        return context


class EmailLoginView(LoginView):
    template_name = "registration/login.html"
    authentication_form = EmailAuthenticationForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["student_count"] = User.objects.count()
        context["course_count"] = Course.objects.count()
        return context


@login_required
def update_profile(request):
    user = request.user
    profile = user.profile

    if request.method == "POST":
        form = ProfileUpdateForm(request.POST)
        if form.is_valid():
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.email = form.cleaned_data["email"]
            user.save()
            profile.middle_name = form.cleaned_data["middle_name"]
            profile.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("update_profile")
    else:
        form = ProfileUpdateForm(initial={
            "first_name": user.first_name,
            "middle_name": profile.middle_name,
            "last_name": user.last_name,
            "email": user.email,
        })

    return render(request, "registration/update_profile.html", {"form": form})