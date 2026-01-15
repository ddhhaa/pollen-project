import openmeteo_requests
from datetime import date, timedelta, datetime
import numpy as np
from collections import defaultdict
from app.models import PollenType, PollenData
from .views import TEST_DATE

openmeteo = openmeteo_requests.Client()

def fetch_pollen_data(latitude: float, longitude: float, city: str):
    pollen_types = PollenType.objects.all()
    if not pollen_types.exists():
        print("No pollen types in DB")
        return

    today = TEST_DATE
    start_date = today
    end_date = today + timedelta(days=6)  # 7 дней

    hourly_params = [p.openmeteo_code for p in pollen_types]

    # Запрос к API
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

    # Берем первую временную метку (API может вернуть только первую)
    first_ts = hourly.Time()
    if hasattr(first_ts, '__iter__'):
        first_ts = first_ts[0]

    # Словарь для хранения данных по типам пыльцы
    pollen_data_dict = {}
    n_hours = None  # количество часов данных

    # Собираем данные для каждого типа пыльцы
    for idx, pollen_type in enumerate(pollen_types):
        try:
            variable = hourly.Variables(idx)
            values = variable.ValuesAsNumpy()
            if n_hours is None:
                n_hours = len(values)
            elif len(values) != n_hours:
                print(f"Предупреждение: {pollen_type.openmeteo_code} имеет {len(values)} значений вместо {n_hours}")

            pollen_data_dict[pollen_type.id] = {
                'type': pollen_type,
                'values': values,
                'name': pollen_type.openmeteo_code
            }

            print(f"{pollen_type.openmeteo_code}: первые 10 значений: {values[:10]}")

        except Exception as e:
            print(f"Ошибка при получении данных для {pollen_type.openmeteo_code}: {e}")
            continue

    if n_hours is None or n_hours == 0:
        print("Нет данных для обработки")
        return

    # Генерируем временные метки по часам
    time_array = np.array([first_ts + 3600 * i for i in range(n_hours)])

    # Словарь для группировки данных по дате/часу
    data_to_update = defaultdict(list)

    for i, timestamp in enumerate(time_array):
        real_dt = datetime.fromtimestamp(timestamp)
        # Корректировка по today (если нужно)
        shift = today - real_dt.date()
        dt = real_dt + timedelta(days=shift.days)

        date_key = dt.date()
        hour_key = dt.hour

        for pollen_id, pollen_info in pollen_data_dict.items():
            if i >= len(pollen_info['values']):
                continue
            value = pollen_info['values'][i]

            data_to_update[(pollen_info['type'], date_key, hour_key, city)].append({
                'concentration': float(value),
                'latitude': latitude,
                'longitude': longitude
            })

    # Обновление/создание записей в базе
    updated_count = 0
    created_count = 0

    for key, data_list in data_to_update.items():
        pollen_type_obj, date_obj, hour_val, city_str = key

        if data_list:
            data = data_list[0]  # можно брать среднее, если есть дубли
            obj, created = PollenData.objects.update_or_create(
                pollen_type=pollen_type_obj,
                date=date_obj,
                hour=hour_val,
                city=city_str,
                defaults={
                    "concentration": data['concentration'],
                    "latitude": latitude,
                    "longitude": longitude,
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

    print(f"Создано записей: {created_count}, обновлено: {updated_count}")
    return created_count + updated_count