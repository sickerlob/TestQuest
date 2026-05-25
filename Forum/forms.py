from django import forms
from django.core.exceptions import ValidationError
from .models import User

class RegistrationForm(forms.Form):
    email = forms.EmailField(max_length=100, label="Email")
    name = forms.CharField(max_length=50, label="Имя")
    lastname = forms.CharField(max_length=50, label="Фамилия")
    fathername = forms.CharField(max_length=50, required=False, label="Отчество")
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Повторите пароль")

    def clean_email(self):
        email = self.cleaned_data.get('email').lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким Email уже зарегистрирован.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise ValidationError("Пароли не совпадают.")
        return cleaned_data


class LoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")