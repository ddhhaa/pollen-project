from django.shortcuts import render, redirect
from .models import PollenData, UserProfile, PollenType, UserAllergy
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegisterForm, CITIES, CITY_COORDINATES
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from collections import defaultdict
from app.pollen_forecast import monthly_pollen_forecast
from django.conf import settings

@login_required(login_url='/login/')
def home(request):

    period = request.GET.get('period', 'day')
    pollen_type_id = request.GET.get('pollen_type')

    today = settings.TEST_DATE
    current_hour = settings.TEST_HOUR

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
    
    # ---------- пользователь ----------
    user_profile = UserProfile.objects.get(user=request.user)
    user_city = user_profile.city

    user_allergy_types = list(
        PollenType.objects.filter(
            id__in=user_profile.allergies.values_list(
                "pollen_type_id", flat=True
            )
        )
    )
    
    # ---------- базовый queryset ----------
    data = PollenData.objects.filter(
        date__range=(start_date, end_date),
        city=user_city
    ).order_by('date', 'hour')

    if user_allergy_types:
        pollen_types_for_chart = user_allergy_types
    else:
        pollen_types_for_chart = PollenType.objects.all()


    data = data.order_by('date', 'hour')

    context = {}

    # ---------- данные для графика по типам пыльцы ----------
    chart_data = []

    for pt in pollen_types_for_chart:
        if period == 'month':
            continue
        type_name = pt.name
        color = pt.color
        points = []

        if period == 'day':
            # данные по часам
            day_data = data.filter(pollen_type=pt, date=today, hour__gte=current_hour, hour__lte=current_hour+5).order_by('hour')
            for rec in day_data:
                points.append({
                    'x': f"{rec.hour:02d}:00",
                    'y': rec.concentration
                })  

        elif period == 'week':
            # среднее за день
            current_date = start_date
            while current_date <= end_date:
                day_records = data.filter(pollen_type=pt, date=current_date)
                concentrations = [r.concentration for r in day_records]
                value = sum(concentrations)/len(concentrations) if concentrations else 0
                points.append({
                    'x': current_date.strftime('%d.%m'),
                    'y': value
                })
                current_date += timedelta(days=1)

        chart_data.append({
            'label': type_name,
            'data': points,
            'borderColor': color,
            'backgroundColor': color,
            'fill': False
        })

    # ---------- прогноз на месяц ----------
    if period == 'month':
        for pt in pollen_types_for_chart:
            points = []
            
            # ---реальные данные ---
            actual_points = []

            current_date = start_date

            while current_date <= min(today, end_date):
                day_records = data.filter(
                    pollen_type=pt,
                    date=current_date
                )

                values = [r.concentration for r in day_records]
                value = sum(values) / len(values) if values else 0

                actual_points.append({
                    'x': current_date.strftime('%d.%m'),
                    'y': value
                })

                current_date += timedelta(days=1)



            # ---прогноз---
            forecast_points = []

            forecast_values = monthly_pollen_forecast(pt, today.month)

            for i in range(1, 31):
                target_date = today + timedelta(days=i)

                value = forecast_values[i % len(forecast_values)]['value']

                forecast_points.append({
                    'x': target_date.strftime('%d.%m'),
                    'y': value
                })


            
            if actual_points:
                chart_data.append({
                    'label': pt.name,
                    'data': actual_points,
                    'borderColor': pt.color,
                    'backgroundColor': pt.color,
                    'fill': False
                })

            if forecast_points:
                chart_data.append({
                    'label': f"{pt.name} (прогноз)",
                    'data': forecast_points,
                    'borderColor': pt.color,
                    'backgroundColor': pt.color,
                    'fill': False,
                    'borderDash': [6, 6]
                })

    context['chart_data'] = chart_data

    data_dict = defaultdict(lambda: defaultdict(list))
    
    for item in data:
        key = f"{item.date.strftime('%Y-%m-%d')}_{item.hour:02d}"
        data_dict[item.date][item.hour].append({
            'pollen_type': item.pollen_type.name,
            'concentration': item.concentration,
            'hour': item.hour,
            'city': item.city
        })
    
    data_by_type = defaultdict(list)
    for item in data:
        data_by_type[item.pollen_type.name].append({
            'date': item.date,
            'hour': item.hour,
            'concentration': item.concentration
        })

    context = {
        "data": data,
        "data_dict": dict(data_dict),
        "data_by_type": dict(data_by_type),
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