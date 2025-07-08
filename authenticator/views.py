# for templates go to Prep_Tester/templates/user_log

from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages # Import the messages framework
from django.contrib.auth.decorators import login_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                if not user.profile.branch:
                    return redirect('branch_selection')
                return redirect('dashboard')
        # No else needed here - form.errors will be handled by the template
    return render(request, 'authenticator/auth.html', {
        'form': form,
        'is_login_page': True
    })

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = UserCreationForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Account created successfully for {user.username}! Please select your branch.")
            return redirect('branch_selection')
    return render(request, 'authenticator/auth.html', {
        'form': form,
        'is_signup_page': True
    })

@login_required(login_url='/login/')
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')
