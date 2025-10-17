from django import forms
from .models import AppUser

class AppUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = AppUser
        fields = ['first_name', 'last_name', 'email', 'password']
