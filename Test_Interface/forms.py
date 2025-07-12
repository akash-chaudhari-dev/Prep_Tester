# Test_Interface/forms.py

from django import forms
from django.contrib.auth import get_user_model
from .models import UserProfile, Branch # Import UserProfile and Branch

User = get_user_model()

class BranchSelectionForm(forms.Form):
    """
    Form for users to select their engineering branch.
    """
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all().order_by('name'),
        empty_label="Chnage Your Branch",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Your Branch"
    )

class UserProfileForm(forms.ModelForm):
    # Example for choices if you want dropdowns
    BRANCH_CHOICES = [
        ('CSE', 'Computer Science Engineering'),
        ('IT', 'Information Technology'),
        ('ENTC', 'Electronics & Telecommunication Engineering'),
        ('MECH', 'Mechanical Engineering'),
        # Add more branches as needed
    ]
    academic_year_CHOICES = [
        ('1st', 'First Year'),
        ('2nd', 'Second Year'),
        ('3rd', 'Third Year'),
        ('4th', 'Final Year'),
    ]

    # These fields must exist on your User model or a related UserProfile model
    # 'name' is a custom field for full name, will be split into first_name/last_name
    name = forms.CharField(max_length=100, required=False, help_text="Your full name")
    # Use ModelChoiceField for branch if you want a dropdown of existing Branch objects
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all().order_by('name'),
        empty_label="Select your Branch",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Branch"
    )
    academic_year = forms.ChoiceField(choices=academic_year_CHOICES, required=False, label="Academic academic_year")
    mobile_number = forms.CharField(max_length=15, required=False, help_text="e.g., +919876543210", label="Mobile Number")

    # New field for file upload - this is NOT directly mapped to a model field in Meta
    profile_picture_upload = forms.ImageField(required=False, label="Upload New Profile Picture")

    class Meta:
        model = UserProfile # Link to your UserProfile model
        # Fields that will be directly saved by ModelForm
        fields = ['branch', 'profile_picture_url'] # profile_picture_url is now a model field

    def __init__(self, *args, **kwargs):
        # Pass the User instance to the form for initial data and saving User fields
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Initialize fields from the User model and UserProfile
        if self.user:
            # Set initial name from User model
            self.fields['name'].initial = f"{self.user.first_name} {self.user.last_name}".strip()
            
            # Set initial values from UserProfile
            if self.instance:
                self.fields['mobile_number'].initial = self.instance.mobile_number or ''
                self.fields['academic_year'].initial = self.instance.academic_year or ''
            # Note: branch field's initial value is handled automatically by ModelChoiceField

        # Apply Bootstrap form-control/form-select class to all fields
        for field_name, field in self.fields.items():
            if field_name not in ['branch', 'profile_picture_upload']: # Branch already has form-select
                field.widget.attrs.update({'class': 'form-control'})
            elif field_name == 'profile_picture_upload':
                field.widget.attrs.update({'class': 'form-control'}) # File input also uses form-control

    def clean_email(self):
        email = self.cleaned_data['email']
        # Ensure email is unique for other users, but allow current user's email
        if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("This email is already in use by another account.")
        return email

    def save(self, commit=True):
        # Save UserProfile fields first
        profile = super().save(commit=False)

        # Update User model fields (first_name, last_name)
        user = self.user
        if 'name' in self.cleaned_data:
            full_name = self.cleaned_data['name'].split(' ', 1)
            user.first_name = full_name[0]
            user.last_name = full_name[1] if len(full_name) > 1 else ''
            if commit:
                user.save() # Save the User model changes

        # Save mobile_number and academic_year if they are on UserProfile
        if 'mobile_number' in self.cleaned_data:
            profile.mobile_number = self.cleaned_data['mobile_number']
        if 'academic_year' in self.cleaned_data:
            profile.academic_year = self.cleaned_data['academic_year']

        if commit:
            profile.save() # Save the UserProfile model changes
        return profile

class AccountSettingsForm(forms.ModelForm):
    """Form for updating sensitive account information like username and email"""
    
    class Meta:
        model = User
        fields = ['username', 'email']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['email'].widget.attrs.update({'class': 'form-control'})

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already in use by another account.")
        return email

