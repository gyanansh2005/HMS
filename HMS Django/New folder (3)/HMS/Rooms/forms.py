from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User
from .models import Student


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(max_length=254, required=True)
    roll_number = forms.CharField(max_length=20, required=True)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'roll_number')

    def clean_roll_number(self):
        roll_number = self.cleaned_data['roll_number']
        # if Student.objects.filter(roll_number=roll_number).exists():
        #     raise forms.ValidationError("This roll number is already registered.")
        return roll_number

class UserEditForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ('roll_number',)
        
        
class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = ('roll_number', 'gender', 'contact_number', 'address', 'profile_picture')