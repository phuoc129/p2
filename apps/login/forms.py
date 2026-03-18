from django import forms
from django.contrib.auth.forms import AuthenticationForm

class TaiKhoanLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'field-input', 
        'placeholder': 'Tên đăng nhập'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'field-input',
        'placeholder': 'Mật khẩu'
    }))