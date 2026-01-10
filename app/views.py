from django.shortcuts import render
from .models import PollenData


def home(request):
    period = request.GET.get('period', 'day')

    if period == 'week':
        data = PollenData.objects.all()[:7]
    elif period == 'month':
        data = PollenData.objects.all()[:30]
    else:
        data = PollenData.objects.all()[:1]

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
