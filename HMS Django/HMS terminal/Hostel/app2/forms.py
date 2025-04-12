from django import forms
from .models import MessMenu, MessRules

class MessMenuForm(forms.ModelForm):
    class Meta:
        model = MessMenu
        fields = ['day', 'meal_type', 'menu']
        widgets = {
            'day': forms.Select(choices=[
                ('Monday', 'Monday'),
                ('Tuesday', 'Tuesday'),
                ('Wednesday', 'Wednesday'),
                ('Thursday', 'Thursday'),
                ('Friday', 'Friday'),
                ('Saturday', 'Saturday'),
                ('Sunday', 'Sunday'),
            ]),
            'meal_type': forms.Select(choices=[
                ('Breakfast', 'Breakfast'),
                ('Lunch', 'Lunch'),
                ('Dinner', 'Dinner'),
            ]),
            'menu': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter menu details...'}),
        }

class MessRulesForm(forms.ModelForm):
    class Meta:
        model = MessRules
        fields = ['rule', 'order']
        widgets = {
            'rule': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter mess rule...'}),
            'order': forms.NumberInput(attrs={'min': 0}),
        }
        
        
# app2/forms.py
from django import forms
from .models import DiscussionMessage

class DiscussionForm(forms.ModelForm):
    class Meta:
        model = DiscussionMessage
        fields = ['message', 'is_notification']
        widgets = {
            'message': forms.TextInput(attrs={
                'placeholder': 'Type message...',
                'class': 'form-control'
            }),
            'is_notification': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if not user or not user.is_staff:
            del self.fields['is_notification']
        
        
