from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate

# def signup_view(request):
#     if request.method == 'POST':
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             login(request, user)
#             return redirect('/')
#     else:
#         form = UserCreationForm()
#     return render(request, 'user_log/signup.html', {'form': form})

# def login_view(request):
#     if request.method == 'POST':
#         form = AuthenticationForm(data=request.POST)
#         if form.is_valid():
#             user = form.get_user()
#             login(request, user)
#             return redirect('/test')
#     else:
#         form = AuthenticationForm()
#     return render(request, 'user_log/login.html', {'form': form})

# def logout_view(request):
#     logout(request)
#     return redirect('/')

# views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib import messages # Import the messages framework

def login_view(request):
    # If the user is already authenticated, redirect them away from the login page
    if request.user.is_authenticated:
        return redirect('branch_selection') # Redirect to your home page or dashboard

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            print(username,password)
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                return redirect('/') # Redirect to your home page or dashboard
            else:
                messages.error(request, "Invalid username or password.")
        else:
            # Form is not valid (e.g., empty fields, incorrect format)
            # Django's form.errors will contain specific field errors
            # For non-field errors (like wrong credentials), it will be in non_field_errors
            messages.error(request, "Please correct the errors below.")
    else:
        # GET request: display an empty login form
        form = AuthenticationForm()

    # Pass the form to the template. The template will handle displaying errors.
    
    return render(request, 'user_log/signup.html', {'form': form, 'is_login_page': True})

def signup_view(request):
    # If the user is already authenticated, redirect them away from the signup page
    if request.user.is_authenticated:
        return redirect('dashboard') # Redirect to your home page or dashboard

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() # Save the new user
            login(request, user) # Log the user in immediately after signup (optional)
            messages.success(request, f"Account created successfully for {user.username}! You are now logged in.")
            return redirect('login') # Redirect to home or a welcome page
        else:
            # Form is not valid (e.g., password mismatch, weak password)
            messages.error(request, "Please correct the errors below to create an account.")
    else:
        # GET request: display an empty signup form
        form = UserCreationForm()

    # Pass the form to the template. The template will handle displaying errors.
    return render(request, 'user_log/signup.html', {'form': form, 'is_signup_page': True})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login') # Redirect to the login page after logout

# A placeholder home view
# def home_view(request):
#     return render(request, 'home.html') # You'll need to create a home.html template