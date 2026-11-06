from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User


class UserRegisterForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "First name", "class": "form-input", "autocomplete": "given-name"})
    )
    last_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Last name", "class": "form-input", "autocomplete": "family-name"})
    )
    username = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={"placeholder": "Username", "class": "form-input", "autocomplete": "username"})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"placeholder": "Email address", "class": "form-input", "autocomplete": "email"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password (min 6 characters)", "class": "form-input", "autocomplete": "new-password"}),
        min_length=6
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Confirm password", "class": "form-input", "autocomplete": "new-password"})
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "username", "email", "password"]

    def clean_username(self):
        username = self.cleaned_data.get("username").strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken. Please choose another.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email").strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned_data


class UserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"placeholder": "Username or email", "class": "form-input", "autocomplete": "username"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Password", "class": "form-input", "autocomplete": "current-password"})
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username", "").strip()
        password = cleaned_data.get("password", "")

        if username and password:
            # Allow login via username or email
            user = authenticate(username=username, password=password)
            if not user:
                # Check if email was supplied instead of username
                user_obj = User.objects.filter(email__iexact=username).first()
                if user_obj:
                    user = authenticate(username=user_obj.username, password=password)

            if not user:
                raise forms.ValidationError("Invalid credentials. Please verify your username/email and password.")
            if not user.is_active:
                raise forms.ValidationError("This account has been deactivated.")
            cleaned_data["user"] = user
        return cleaned_data
