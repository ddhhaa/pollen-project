from datetime import timedelta
from .models import PollenData, PollenType, UserProfile
from app.pollen_forecast import monthly_pollen_forecast


def get_period_dates(today, period):
    if period == 'week':
        return today, today + timedelta(days=6)
    if period == 'month':
        return today, today + timedelta(days=29)
    return today, today

def get_user_context(user):
    profile = UserProfile.objects.get(user=user)

    allergy_types = list(
        PollenType.objects.filter(
            id__in=profile.allergies.values_list('pollen_type_id', flat=True)
        )
    )

    pollen_types = allergy_types if allergy_types else PollenType.objects.all()

    return {
        'profile': profile,
        'city': profile.city,
        'pollen_types': pollen_types,
        'allergy_types': allergy_types,
    }

def get_base_queryset(start_date, end_date, city):
    return (
        PollenData.objects
        .filter(date__range=(start_date, end_date), city=city)
        .order_by('date', 'hour')
    )

def build_day_chart(data, pollen_types, today, current_hour):
    chart = []

    for pt in pollen_types:
        points = [
            {'x': f'{r.hour:02d}:00', 'y': r.concentration}
            for r in data.filter(
                pollen_type=pt,
                date=today,
                hour__gte=current_hour,
                hour__lte=current_hour + 5
            )
        ]

        chart.append({
            'label': pt.name,
            'data': points,
            'borderColor': pt.color,
            'backgroundColor': pt.color,
            'fill': False
        })

    return chart

def build_week_chart(data, pollen_types, start_date, end_date):
    chart = []

    for pt in pollen_types:
        points = []
        current = start_date

        while current <= end_date:
            values = list(
                data.filter(pollen_type=pt, date=current)
                .values_list('concentration', flat=True)
            )

            points.append({
                'x': current.strftime('%d.%m'),
                'y': sum(values) / len(values) if values else 0
            })

            current += timedelta(days=1)

        chart.append({
            'label': pt.name,
            'data': points,
            'borderColor': pt.color,
            'backgroundColor': pt.color,
            'fill': False
        })

    return chart

def build_month_chart(data, pollen_types, today, end_date):
    chart = []

    for pt in pollen_types:
        # реальные
        actual = []
        current = today

        while current <= today:
            values = list(
                data.filter(pollen_type=pt, date=current)
                .values_list('concentration', flat=True)
            )

            actual.append({
                'x': current.strftime('%d.%m'),
                'y': sum(values) / len(values) if values else 0
            })

            current += timedelta(days=1)

        # прогноз
        forecast = []
        forecast_values = monthly_pollen_forecast(pt, today.month)

        for i in range(1, 31):
            date_point = today + timedelta(days=i)
            value = forecast_values[i % len(forecast_values)]['value']

            forecast.append({
                'x': date_point.strftime('%d.%m'),
                'y': value
            })

        chart.append({
            'label': pt.name,
            'data': actual,
            'borderColor': pt.color,
            'fill': False
        })

        chart.append({
            'label': f'{pt.name} (прогноз)',
            'data': forecast,
            'borderColor': pt.color,
            'borderDash': [6, 6],
            'fill': False
        })

    return chart
