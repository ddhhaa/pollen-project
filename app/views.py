from django.shortcuts import render, redirect
from .models import PollenData, UserProfile, PollenType, UserAllergy
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from django.db.models import Avg
from collections import defaultdict

TEST_DATE = date(2025, 4, 15)
TEST_HOUR = 10

@login_required(login_url='/login/')
def home(request):

    period = request.GET.get('period', 'day')
    pollen_type_id = request.GET.get('pollen_type')

    today = TEST_DATE
    current_hour = TEST_HOUR

    # ---------- тип пыльцы ----------
    selected_pollen_type = None
    if pollen_type_id:
        selected_pollen_type = PollenType.objects.filter(id=pollen_type_id).first()

    # ---------- период ----------
    if period == 'week':
        start_date = today
        end_date = today + timedelta(days=6)
    elif period == 'month':
        start_date = today
        end_date = today + timedelta(days=29)
    else:
        start_date = today
        end_date = today
    
    # ---------- базовый queryset ----------
    data = PollenData.objects.filter(
        date__range=(start_date, end_date)
    )

    if selected_pollen_type:
        data = data.filter(pollen_type=selected_pollen_type)

    data = data.order_by('date', 'hour')

    # ---------- данные для графика ----------
    chart_data = []

    if period == 'day':
        # Создаем словарь для хранения данных по часам
        hour_data = defaultdict(list)
        
        # Собираем данные по часам
        for item in data.filter(date=today):
            hour_data[item.hour].append(item.concentration)
        
        # Определяем стартовый час
        available_hours = sorted(hour_data.keys())
        start_hour = current_hour if current_hour in available_hours else (available_hours[0] if available_hours else current_hour)
        
        # Формируем данные для графика
        for i in range(6):
            hour = start_hour + i
            concentrations = hour_data.get(hour, [])
            
            # Если есть данные для этого часа, берем среднее (или первое значение)
            if concentrations:
                # Для одного типа пыльцы - первое значение, для нескольких - среднее
                value = sum(concentrations) / len(concentrations)
            else:
                value = 0
            
            chart_data.append({
                "label": f"{hour:02d}:00",
                "value": round(value, 2),
                "date": today,
                "hour": hour
            })

    else:
        # Создаем словарь для хранения данных по дням
        day_data = defaultdict(list)
        
        # Собираем данные по дням
        for item in data:
            day_data[item.date].append(item.concentration)
        
        # Формируем данные для графика по дням
        current_date = start_date
        while current_date <= end_date:
            concentrations = day_data.get(current_date, [])
            
            if concentrations:
                # Средняя концентрация за день
                value = sum(concentrations) / len(concentrations)
            else:
                value = 0
            
            chart_data.append({
                "label": current_date.strftime('%d.%m'),
                "value": round(value, 2),
                "date": current_date
            })
            
            current_date += timedelta(days=1)

    # ---------- пользователь ----------
    user_profile = UserProfile.objects.get(user=request.user)
    user_allergy_types = [
        allergy.pollen_type for allergy in user_profile.allergies.all()
    ]

    # Преобразуем QuerySet в словарь для удобства отображения
    # Группируем данные по дате и часу
    data_dict = defaultdict(lambda: defaultdict(list))
    
    for item in data:
        key = f"{item.date.strftime('%Y-%m-%d')}_{item.hour:02d}"
        data_dict[item.date][item.hour].append({
            'pollen_type': item.pollen_type.name,
            'concentration': item.concentration,
            'hour': item.hour,
            'city': item.city
        })
    
    # Или альтернативный формат - по типам пыльцы
    data_by_type = defaultdict(list)
    for item in data:
        data_by_type[item.pollen_type.name].append({
            'date': item.date,
            'hour': item.hour,
            'concentration': item.concentration
        })

    context = {
        "data": data,  # Оригинальный QuerySet
        "data_dict": dict(data_dict),  # Словарь по датам и часам
        "data_by_type": dict(data_by_type),  # Словарь по типам пыльцы
        "chart_data": chart_data,
        "period": period,
        "today_date": today,
        "start_date": start_date,
        "end_date": end_date,
        "current_hour": current_hour if period == 'day' else None,
        "selected_pollen_type": selected_pollen_type,
        "all_pollen_types": PollenType.objects.all(),
        "user_allergy_types": user_allergy_types,
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