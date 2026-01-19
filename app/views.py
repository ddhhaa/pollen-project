from django.shortcuts import render, redirect
from .models import PollenData, UserProfile, PollenType, UserAllergy
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm, CITIES, CITY_COORDINATES
from django.contrib.auth.decorators import login_required
from django.conf import settings
from app.pollen_charts import (
    get_period_dates,
    get_user_context,
    get_base_queryset,
    build_day_chart,
    build_week_chart,
    build_month_chart,
)


@login_required(login_url='/login/')
@login_required(login_url='/login/')
def home(request):
    period = request.GET.get('period', 'day')

    today = settings.TEST_DATE
    current_hour = settings.TEST_HOUR

    start_date, end_date = get_period_dates(today, period)
    user_ctx = get_user_context(request.user)

    data = get_base_queryset(start_date, end_date, user_ctx['city'])

    if period == 'day':
        chart_data = build_day_chart(
            data, user_ctx['pollen_types'], today, current_hour
        )
    elif period == 'week':
        chart_data = build_week_chart(
            data, user_ctx['pollen_types'], start_date, end_date
        )
    else:
        chart_data = build_month_chart(
            data, user_ctx['pollen_types'], today, end_date
        )

    return render(request, 'home.html', {
        'chart_data': chart_data,
        'period': period,
        'today_date': today,
        'start_date': start_date,
        'end_date': end_date,
        'current_hour': current_hour if period == 'day' else None,
        'user_allergy_types': user_ctx['allergy_types'],
        'all_pollen_types': PollenType.objects.all(),
    })


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            city = form.cleaned_data.get("city")
            coordinates = CITY_COORDINATES.get(city, {'latitude': 55.7558, 'longitude': 37.6176})
            
            UserProfile.objects.create(
                user=user,
                age=form.cleaned_data.get("age"),
                city=city,
                latitude=coordinates['latitude'],
                longitude=coordinates['longitude']
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
        selected_ids = request.POST.getlist('allergies')
        user_profile.allergens.clear()
        
        for pollen_id in selected_ids:
            pollen_type = PollenType.objects.get(id=pollen_id)
            UserAllergy.objects.create(
                user=user_profile,
                pollen_type=pollen_type,
                sensitivity=3
            )
        if 'city' in request.POST:
                city = request.POST.get('city')
                coordinates = CITY_COORDINATES.get(city, {'latitude': 55.7558, 'longitude': 37.6176})
                
                user_profile.city = city
                user_profile.latitude = coordinates['latitude']
                user_profile.longitude = coordinates['longitude']
                user_profile.save()

        return redirect('profile')
    
    return render(request, 'profile.html', {
        'user_profile': user_profile,
        'all_pollen': all_pollen_types,
        'user_allergies': user_allergies,
        'cities': CITIES,
    })