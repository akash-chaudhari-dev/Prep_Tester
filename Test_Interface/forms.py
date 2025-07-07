# Test_Interface/forms.py

from django import forms
from .models import Branch

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



# Test_Interface/forms.py
from django import forms
from django.contrib.auth import get_user_model
from .models import UserProfile, Branch # Import UserProfile and Branch

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    # Example for choices if you want dropdowns
    BRANCH_CHOICES = [
        ('CSE', 'Computer Science Engineering'),
        ('IT', 'Information Technology'),
        ('ENTC', 'Electronics & Telecommunication Engineering'),
        ('MECH', 'Mechanical Engineering'),
        # Add more branches as needed
    ]
    # YEAR_CHOICES = [
    #     ('1st', 'First Year'),
    #     ('2nd', 'Second Year'),
    #     ('3rd', 'Third Year'),
    #     ('4th', 'Final Year'),
    # ]

    # These fields must exist on your User model or a related UserProfile model
    # 'name' is a custom field for full name, will be split into first_name/last_name
    name = forms.CharField(max_length=100, required=False, help_text="Your full name")
    email = forms.EmailField(required=True)
    # Use ModelChoiceField for branch if you want a dropdown of existing Branch objects
    branch = forms.ModelChoiceField(
        queryset=Branch.objects.all().order_by('name'),
        empty_label="Select your Branch",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Branch"
    )
    # year = forms.ChoiceField(choices=YEAR_CHOICES, required=False, label="Academic Year")
    # mobile_number = forms.CharField(max_length=15, required=False, help_text="e.g., +919876543210", label="Mobile Number")

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

        # Initialize 'name', 'email', 'mobile_number', 'year' from the User model (or UserProfile if they are there)
        if self.user:
            self.fields['name'].initial = f"{self.user.first_name} {self.user.last_name}".strip()
            self.fields['email'].initial = self.user.email
            # Assuming mobile_number and year are on UserProfile
            # self.fields['mobile_number'].initial = self.instance.mobile_number if self.instance else ''
            # self.fields['year'].initial = self.instance.year if self.instance else ''
            # For branch, ModelChoiceField handles initial selection automatically if instance.branch is set

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

        # Update User model fields (first_name, last_name, email)
        user = self.user
        if 'name' in self.cleaned_data:
            full_name = self.cleaned_data['name'].split(' ', 1)
            user.first_name = full_name[0]
            user.last_name = full_name[1] if len(full_name) > 1 else ''
        
        if 'email' in self.cleaned_data:
            user.email = self.cleaned_data['email']
            user.username = self.cleaned_data['email'] # Often email is used as username

        # Save mobile_number and year if they are on UserProfile
        # if 'mobile_number' in self.cleaned_data:
        #     profile.mobile_number = self.cleaned_data['mobile_number']
        # if 'year' in self.cleaned_data:
        #     profile.year = self.cleaned_data['year']

        if commit:
            user.save() # Save the User model changes
            profile.save() # Save the UserProfile model changes
        return profile

