from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

CITIES = [
    ('', 'Выберите город'),
    ('Москва', 'Москва'),
    ('Санкт-Петербург', 'Санкт-Петербург'),
    ('Нижний Новгород', 'Нижний Новгород'),
    ('Калининград', 'Калининград'),
    ('Париж', 'Париж'),
    ('Лондон', 'Лондон'),
    ('Нью-Йорк', 'Нью-Йорк'),
]

CITY_COORDINATES = {
    'Москва': {'latitude': 55.7558, 'longitude': 37.6176},
    'Санкт-Петербург': {'latitude': 59.9343, 'longitude': 30.3351},
    'Нижний Новгород': {'latitude': 56.3269, 'longitude': 44.0065},
    'Калининград': {'latitude': 54.7104, 'longitude': 20.4522},
    'Париж': {'latitude': 48.8566, 'longitude': 2.3522},
    'Лондон': {'latitude': 51.5074, 'longitude': -0.1278},
    'Нью-Йорк': {'latitude': 40.7128, 'longitude': -74.0060},
}

class RegisterForm(UserCreationForm):
    age = forms.IntegerField(
        required=False,
        label="Возраст",
        widget=forms.NumberInput(attrs={"placeholder": "Ваш возраст"})
    )

    city = forms.ChoiceField(
        required=True,
        label="Город проживания",
        choices=CITIES,
        widget=forms.Select(attrs={"class": "form-select"})
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
