# views.py - правильные импорты
from django.shortcuts import render, redirect
from .models import PollenData, UserProfile, PollenType, UserAllergy
from .open_meteo import fetch_pollen_data
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required

@login_required(login_url='/login/')
def home(request):

    period = request.GET.get('period', 'day')

    if period == 'week':
        data = PollenData.objects.order_by('-date', '-hour')[:7]
    elif period == 'month':
        data = PollenData.objects.order_by('-date', '-hour')[:30]
    else:
        data = PollenData.objects.order_by('-date', '-hour')[:1]

    chart_data = [
        {
            "date": item.date.strftime('%Y-%m-%d'),
            "value": item.concentration
        }
        for item in data
    ]

    context = {
        "data": data,
        "chart_data": chart_data,
        "period": period,
    }

    return render(request, "home.html", context)

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            # создаём профиль
            UserProfile.objects.create(
                user=user,
                age=form.cleaned_data.get("age"),
                city=form.cleaned_data.get("city"),
            )

            login(request, user)
            return redirect("home")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("home")
    else:
        form = AuthenticationForm()
    return render(request, "login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("home")

@login_required
def profile(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Получаем аллергии пользователя
    user_allergies = user_profile.allergies.all()
    
    # Получаем все типы пыльцы
    all_pollen_types = PollenType.objects.all()
    
    if request.method == "POST":
        # Обработка выбора аллергенов
        selected_ids = request.POST.getlist('allergies')
        user_profile.allergens.clear()  # Очищаем старые
        
        for pollen_id in selected_ids:
            pollen_type = PollenType.objects.get(id=pollen_id)
            UserAllergy.objects.create(
                user=user_profile,
                pollen_type=pollen_type,
                sensitivity=3
            )
        return redirect('profile')
    
    return render(request, 'profile.html', {
        'user_profile': user_profile,
        'all_pollen': all_pollen_types,
        'user_allergies': user_allergies,
    })