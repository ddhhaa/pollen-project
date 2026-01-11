from django.shortcuts import render
from .models import PollenData
from .open_meteo import fetch_pollen_data


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
