from django.shortcuts import render, redirect
from .models import PollenData, UserProfile
from .open_meteo import fetch_pollen_data
from django.contrib.auth import login
from .forms import RegisterForm

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
