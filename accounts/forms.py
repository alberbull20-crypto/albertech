from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.utils.text import slugify
from .models import Profile


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, required=True, label="First Name",
        widget=forms.TextInput(attrs={"placeholder": "First name", "class": "input-field"}))
    middle_name = forms.CharField(max_length=100, required=False, label="Middle Name",
        widget=forms.TextInput(attrs={"placeholder": "Middle name (optional)", "class": "input-field"}))
    last_name = forms.CharField(max_length=100, required=True, label="Last Name",
        widget=forms.TextInput(attrs={"placeholder": "Last name", "class": "input-field"}))
    email = forms.EmailField(required=True, label="Email Address",
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com", "class": "input-field"}))
    agree_terms = forms.BooleanField(required=True, label="I agree to the Terms of Service and Privacy Policy")

    class Meta:
        model = User
        fields = ("first_name", "middle_name", "last_name", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].widget.attrs.update({"placeholder": "Min 8 characters", "class": "input-field"})
        self.fields["password2"].widget.attrs.update({"placeholder": "Confirm your password", "class": "input-field"})

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]

        base_username = slugify(self.cleaned_data["email"].split("@")[0]) or "user"
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        user.username = username

        if commit:
            user.save()
            Profile.objects.create(user=user, middle_name=self.cleaned_data.get("middle_name", ""))
        return user


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={"placeholder": "you@example.com", "class": "input-field", "autofocus": True}),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Enter your password", "class": "input-field"}),
    )


class ProfileUpdateForm(forms.Form):
    first_name = forms.CharField(max_length=100, required=True,
        widget=forms.TextInput(attrs={"class": "input-field"}))
    middle_name = forms.CharField(max_length=100, required=False,
        widget=forms.TextInput(attrs={"class": "input-field"}))
    last_name = forms.CharField(max_length=100, required=True,
        widget=forms.TextInput(attrs={"class": "input-field"}))
    email = forms.EmailField(required=True,
        widget=forms.EmailInput(attrs={"class": "input-field"}))