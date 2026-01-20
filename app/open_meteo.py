import openmeteo_requests
from datetime import timedelta, datetime
import numpy as np
from collections import defaultdict
from app.models import PollenType, PollenData
from django.conf import settings

openmeteo = openmeteo_requests.Client()


def fetch_pollen_data(latitude: float, longitude: float, city: str):
    pollen_types = PollenType.objects.all()
    if not pollen_types.exists():
        return

    today = settings.TEST_DATE
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

    first_ts = hourly.Time()
    if hasattr(first_ts, "__iter__"):
        first_ts = first_ts[0]

    pollen_data_dict = {}
    n_hours = None

    for idx, pollen_type in enumerate(pollen_types):
        try:
            variable = hourly.Variables(idx)
            values = variable.ValuesAsNumpy()

            if n_hours is None:
                n_hours = len(values)

            pollen_data_dict[pollen_type.id] = {
                "type": pollen_type,
                "values": values,
                "name": pollen_type.openmeteo_code,
            }
        except Exception:
            continue

    if n_hours is None or n_hours == 0:
        return

    time_array = np.array([first_ts + 3600 * i for i in range(n_hours)])
    data_to_update = defaultdict(list)

    for i, timestamp in enumerate(time_array):
        dt = datetime.fromtimestamp(timestamp)

        date_key = dt.date()
        hour_key = dt.hour

        for pollen_info in pollen_data_dict.values():
            if i >= len(pollen_info["values"]):
                continue

            data_to_update[
                (pollen_info["type"], date_key, hour_key, city)
            ].append(
                {
                    "concentration": float(pollen_info["values"][i]),
                    "latitude": latitude,
                    "longitude": longitude,
                }
            )

    updated_count = 0
    created_count = 0

    for key, data_list in data_to_update.items():
        pollen_type_obj, date_obj, hour_val, city_str = key
        data = data_list[0]

        _, created = PollenData.objects.update_or_create(
            pollen_type=pollen_type_obj,
            date=date_obj,
            hour=hour_val,
            city=city_str,
            defaults={
                "concentration": data["concentration"],
                "latitude": latitude,
                "longitude": longitude,
            },
        )

        if created:
            created_count += 1
        else:
            updated_count += 1

    return created_count + updated_count
