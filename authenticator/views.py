# for templates go to Prep_Tester/templates/user_log

from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages # Import the messages framework
from django.contrib.auth.decorators import login_required

class CustomUserCreationForm(forms.ModelForm):
    """Custom form that extends ModelForm to include email field"""
    email = forms.EmailField(required=True)
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

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

    form = CustomUserCreationForm(request.POST or None)
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
    return redirect('signup')

def password_reset_view(request):
    # Get current step from session, default to 1
    current_step = request.session.get('reset_step', 1)
    email = request.session.get('reset_email', '')

    if request.method == 'POST':
        # Step 1: Email submission
        if 'step1' in request.POST:
            email = request.POST.get('email')
            if email:
                try:
                    user = User.objects.get(email=email)
                    # Store email in session
                    request.session['reset_email'] = email
                    request.session['reset_step'] = 2
                    # In a real system, you would send an email with OTP here
                    messages.success(request, "Verification code has been sent to your email.")
                    current_step = 2
                except User.DoesNotExist:
                    messages.error(request, "No account found with that email address.")
            else:
                messages.error(request, "Please enter a valid email address.")

        # Step 2: Verification code
        elif 'step2' in request.POST:
            code = request.POST.get('code')
            if code == '123456':  # Hardcoded for demo, replace with real verification
                request.session['reset_step'] = 3
                current_step = 3
                messages.success(request, "Code verified successfully.")
            else:
                messages.error(request, "Invalid verification code.")

        # Step 2: Resend code
        elif 'resend_code' in request.POST:
            messages.info(request, "New verification code has been sent.")
            # In a real system, you would regenerate and send new OTP here

        # Step 3: Password reset
        elif 'step3' in request.POST:
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            
            if password1 and password2:
                if password1 == password2:
                    try:
                        user = User.objects.get(email=email)
                        user.set_password(password1)
                        user.save()
                        # Clear session data
                        request.session.pop('reset_step', None)
                        request.session.pop('reset_email', None)
                        messages.success(request, "Password has been reset successfully. You can now log in.")
                        return redirect('login')
                    except User.DoesNotExist:
                        messages.error(request, "Error resetting password. Please try again.")
                else:
                    messages.error(request, "Passwords don't match.")
            else:
                messages.error(request, "Please enter both passwords.")

    # Handle GET request or if POST didn't change step
    return render(request, 'authenticator/password_reset.html', {
        'step': current_step,
        'email': email
    })