from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from .models import MenuItem, Category, Table, UserProfile


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Login',
            'autocomplete': 'off'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Parol'
        })
    )
    role = forms.ChoiceField(
        choices=[('waiter', 'Ofitsiant'), ('admin', 'Admin')],
        widget=forms.RadioSelect,
        initial='waiter'
    )


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['name', 'price', 'category', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Taom nomi'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '25000'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'slug']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
        }


class TableForm(forms.ModelForm):
    class Meta:
        model = Table
        fields = ['number', 'is_active']
        widgets = {
            'number': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }


class UserForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=[('waiter', 'Ofitsiant'), ('admin', 'Admin')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Parol'}),
        required=False
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Login'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ism'}),
        }
