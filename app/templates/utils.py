from app.models import PollenData, PollenType
from datetime import date

def get_pollen_chart_data(city: str, start_date: date, end_date: date):
    pollen_types = PollenType.objects.all()
    datasets = []

    for pt in pollen_types:
        data_points = []
        records = PollenData.objects.filter(
            pollen_type=pt,
            city=city,
            date__range=(start_date, end_date)
        ).order_by("date", "hour")

        for rec in records:
            dt_str = f"{rec.date} {rec.hour}:00"
            data_points.append({"x": dt_str, "y": rec.concentration})

        datasets.append({
            "label": pt.name,
            "data": data_points,
            "borderColor": pt.color,
            "backgroundColor": pt.color,
            "fill": False,
        })

    return datasets
