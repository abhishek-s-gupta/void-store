from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from orders.cart import merge_session_cart
from .forms import UserLoginForm, UserRegisterForm


def register_view(request):
    """User registration flow with validation and instant session initialization."""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            old_session_key = request.session.session_key
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()
            # Log the user in directly
            login(request, user)
            # Merge guest cart
            merge_session_cart(user, old_session_key)
            messages.success(request, f"Welcome to VOID STORE, {user.first_name or user.username}. Your account is ready.")
            next_url = request.GET.get("next") or "home"
            return redirect(next_url)
        else:
            messages.error(request, "Please review and correct the errors below.")
    else:
        form = UserRegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    """User login flow supporting username or email."""
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            old_session_key = request.session.session_key
            user = form.cleaned_data["user"]
            login(request, user)
            # Merge guest cart
            merge_session_cart(user, old_session_key)
            messages.success(request, f"Welcome back, {user.first_name or user.username}.")
            next_url = request.GET.get("next") or "home"
            return redirect(next_url)
        else:
            messages.error(request, "Login failed. Please check your username and password.")
    else:
        form = UserLoginForm()

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    """Logs the user out and clears private session data."""
    if request.user.is_authenticated:
        username = request.user.first_name or request.user.username
        logout(request)
        messages.info(request, f"You have been signed out, {username}.")
    return redirect("home")
