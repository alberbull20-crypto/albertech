from django.urls import path
from .views import SignUpView, EmailLoginView, update_profile

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path("login/", EmailLoginView.as_view(), name="login"),
    path("profile/", update_profile, name="update_profile"),
]