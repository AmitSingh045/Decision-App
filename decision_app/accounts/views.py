from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        password2 = request.POST.get('password2', '').strip()

        if not username or not password:
            messages.error(request, "Username and password are required.")
        elif len(password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
        elif password != password2:
            messages.error(request, "Passwords do not match.")
        elif User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
        else:
            User.objects.create_user(username=username, password=password)
            messages.success(request, "Account created! Please login.")
            return redirect('login')
    return render(request, 'register.html')


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        if not username or not password:
            messages.error(request, "Please enter both username and password.")
        else:
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                next_url = request.GET.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, "Invalid username or password.")
    return render(request, 'login.html')


def user_logout(request):
    if request.method == "POST":
        logout(request)
        return redirect('login')
    logout(request)
    return redirect('login')
