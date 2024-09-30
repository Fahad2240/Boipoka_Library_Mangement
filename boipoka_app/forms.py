from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from boipoka_app.models import Borrowing, Subscription,Book

FROM_INPUT_CLASSES='text-slate-300 w-full px-5 py-3 rounded-xl border'

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model=User
        fields=('username','email','password1','password2')
    username=forms.CharField(widget=forms.TextInput(attrs={
        'placeholder':"your_name",
        'class':"rounded bg-gray-300 w-full py-1 px-3 !outline-none"
        }))
    email=forms.CharField(widget=forms.EmailInput(attrs={
        'placeholder':"add_your_email",
        'class':"rounded bg-gray-300 w-full py-1 px-3 !outline-none"
        }))
    password1=forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': "your_password",
        'class':"rounded bg-gray-300 w-full py-1 px-3 !outline-none"
        }))
    
    password2=forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': "confirm_your_password",
        'class':"rounded bg-gray-300 w-full py-1 px-3 !outline-none"
        }))
        

class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['subscription_type']  # Assuming 'tier' is the only field you want the user to select

    subscription_type = forms.ChoiceField(choices=Subscription.TIER_CHOICES, widget=forms.Select(attrs={
        'class': "rounded bg-gray-300 w-full py-1 px-3 !outline-none"
    }))
    
    def __init__(self, *args, **kwargs):
        super(SubscriptionForm, self).__init__(*args, **kwargs)
        

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author', 'description', 'image','availability_status','total_copies','available_copies']
    title=forms.CharField(widget=forms.TextInput(attrs={'class': FROM_INPUT_CLASSES}))
    author=forms.CharField(widget=forms.TextInput(attrs={'class': FROM_INPUT_CLASSES}))
    description=forms.CharField(widget=forms.Textarea(attrs={'class': FROM_INPUT_CLASSES}))
    image=forms.ImageField(widget=forms.FileInput(attrs={'class': FROM_INPUT_CLASSES}))
    availability_status=forms.BooleanField(widget=forms.CheckboxInput(attrs={'class': FROM_INPUT_CLASSES}))
    total_copies=forms.IntegerField(widget=forms.NumberInput(attrs={'class': FROM_INPUT_CLASSES}))
    available_copies=forms.IntegerField(widget=forms.NumberInput(attrs={'class': FROM_INPUT_CLASSES}))
    
    
# class UpdateDueDateForm(forms.ModelForm):
#     class Meta:
#         model = Borrowing
#         fields = ['due_date']  # Include only the due_date field
#     due_date= forms.DateInput(attrs={'type': 'date'}),  # Set input type to date
#         }