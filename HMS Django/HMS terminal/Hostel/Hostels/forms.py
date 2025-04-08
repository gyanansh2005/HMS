from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser,StudentProfile

class SignupForm(UserCreationForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    contact_number = forms.CharField(max_length=15, required=True)  # Add this field
    terms = forms.BooleanField(required=True)

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'roll_number', 'contact_number', 'password1', 'password2')
    
    
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['contact_number', 'profile_picture', 'bio']