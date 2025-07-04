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

