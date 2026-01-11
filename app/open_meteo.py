import openmeteo_requests
from datetime import date, timedelta, datetime
import numpy as np

from app.models import PollenType, PollenData

openmeteo = openmeteo_requests.Client()


def fetch_pollen_data(latitude: float, longitude: float, city: str):
    pollen_types = PollenType.objects.all()
    if not pollen_types.exists():
        print("No pollen types in DB")
        return

    today = date.today()
    start_date = today
    end_date = today + timedelta(days=6)

    hourly_params = [p.openmeteo_code for p in pollen_types]

    responses = openmeteo.weather_api(
        "https://air-quality-api.open-meteo.com/v1/air-quality",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "hourly": hourly_params,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "timezone": "auto",
        },
    )

    response = responses[0]

    hourly = response.Hourly()
    
    # Получаем массив временных меток
    times = hourly.Time()
    
    # Конвертируем в numpy array если нужно
    if hasattr(times, '__iter__'):
        time_array = np.array(times) if not isinstance(times, np.ndarray) else times
    else:
        # Если это скаляр, создаем массив
        time_array = np.array([times])
    
    print(f"Получено временных меток: {len(time_array)}")

    for pollen_type in pollen_types:
        try:
            # Находим индекс переменной
            idx = hourly_params.index(pollen_type.openmeteo_code)
            variable = hourly.Variables(idx)
            values = variable.ValuesAsNumpy()
            
            print(f"{pollen_type.openmeteo_code}: первые 10 значений: {values[:10]}")
            
            # Обрабатываем данные для каждого часа
            for i, value in enumerate(values):
                if i >= len(time_array):  # Защита от выхода за пределы массива
                    break
                    
                dt = datetime.fromtimestamp(time_array[i])
                
                PollenData.objects.update_or_create(
                    pollen_type=pollen_type,
                    date=dt.date(),
                    hour=dt.hour,
                    city=city,
                    latitude=latitude,
                    longitude=longitude,
                    defaults={
                        "concentration": float(value),
                    }
                )
                
        except Exception as e:
            continue
