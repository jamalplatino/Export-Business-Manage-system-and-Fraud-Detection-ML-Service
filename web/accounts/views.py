from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required


def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password2 = request.POST.get('password2', '')

        errors = []
        if not username or not email or not password:
            errors.append('Username, email, and password are required.')
        if password != password2:
            errors.append('Passwords do not match.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if User.objects.filter(username=username).exists():
            errors.append(f'Username "{username}" is already taken.')
        if User.objects.filter(email=email).exists():
            errors.append(f'Email "{email}" is already registered.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            messages.success(request, f'Welcome, {username}!')
            return redirect('customer_list')

    return render(request, 'accounts/signup.html')


@login_required
def profile(request):
    return render(request, 'accounts/profile.html')