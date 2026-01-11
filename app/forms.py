from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):
    age = forms.IntegerField(
        required=False,
        label="Возраст",
        widget=forms.NumberInput(attrs={"placeholder": "Ваш возраст"})
    )

    city = forms.CharField(
        required=False,
        label="Город",
        widget=forms.TextInput(attrs={"placeholder": "Город проживания"})
    )

    username = forms.CharField(
        label="Логин",
        widget=forms.TextInput(attrs={"placeholder": "Придумайте логин"})
    )

    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"placeholder": "Минимум 8 символов"})
    )

    password2 = forms.CharField(
        label="Повторите пароль",
        widget=forms.PasswordInput(attrs={"placeholder": "Повторите пароль"})
    )

    class Meta:
        model = User
        fields = ("username", "password1", "password2", "age", "city")
