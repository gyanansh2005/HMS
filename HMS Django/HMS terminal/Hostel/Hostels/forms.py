from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, StudentProfile, FeePayment, ComplaintMaintenance, Feedback

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
        
        
class CardPaymentForm(forms.Form):
    card_number = forms.CharField(label='Card Number', max_length=19)
    expiry_date = forms.CharField(label='Expiry Date (MM/YY)', max_length=5)
    cvc = forms.CharField(label='CVC', max_length=3)
    
    
class PaymentForm(forms.ModelForm):
    card_number = forms.CharField(label='Card Number', max_length=19, required=True)
    expiry_date = forms.CharField(label='Expiry (MM/YY)', max_length=5, required=True)
    cvc = forms.CharField(label='CVC', max_length=3, required=True)

    class Meta:
        model = FeePayment
        fields = ['amount', 'receipt']
        widgets = {
            'amount': forms.NumberInput(attrs={'readonly': 'readonly'})
        }
        

class ComplaintMaintenanceForm(forms.ModelForm):
    class Meta:
        model = ComplaintMaintenance
        fields = ['request_type', 'room_number', 'category', 'details']

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ['environment_rating', 'service_rating', 'comments', 'hostel']
        

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class StaffSignupForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'roll_number', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_staff = True  # Automatically set as staff
        if commit:
            user.save()
        return user
    
from django import forms
from app2.models import Form

class EventForm(forms.ModelForm):
    class Meta:
        model = Form
        fields = ['name', 'date', 'time', 'venue', 'organizer']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'time': forms.TimeInput(attrs={'type': 'time'}),
        }
