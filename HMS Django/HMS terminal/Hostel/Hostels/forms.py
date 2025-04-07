from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class SignupForm(UserCreationForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    terms = forms.BooleanField(required=True)

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'roll_number', 'password1', 'password2')