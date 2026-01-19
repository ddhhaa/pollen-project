import time
import requests
import pandas as pd
from datetime import date, timedelta, datetime
from django.core.management.base import BaseCommand
from app.models import PollenType, PollenData


class Command(BaseCommand):
    help = "Загрузка и агрегация исторических данных о пыльце по дням без года с логами"

    def add_arguments(self, parser):
        parser.add_argument("--city", type=str, default="Москва")
        parser.add_argument("--latitude", type=float, default=55.7558)
        parser.add_argument("--longitude", type=float, default=37.6173)
        parser.add_argument("--number_of_years_to_load", type=int, default=3)

    def handle(self, *args, **options):
        self.stdout.write("Команда стартовала")
        city_name = options["city"]
        latitude_of_city = options["latitude"]
        longitude_of_city = options["longitude"]
        number_of_years_to_load = options["number_of_years_to_load"]

        list_of_all_pollen_types = list(PollenType.objects.all())
        if not list_of_all_pollen_types:
            self.stdout.write(self.style.ERROR("Нет типов пыльцы в базе"))
            return

        self.stdout.write(f"Найдено типов пыльцы: {len(list_of_all_pollen_types)}")
        for pollen_type_instance in list_of_all_pollen_types:
            self.stdout.write(f"  - {pollen_type_instance.name} ({pollen_type_instance.openmeteo_code})")

        list_of_rows_from_api = []

        current_date_today = date.today()

        for year_offset in range(number_of_years_to_load):
            year_to_load = current_date_today.year - year_offset - 1
            start_date_of_season = date(year_to_load, 3, 1)
            end_date_of_season = date(year_to_load, 10, 31)

            self.stdout.write(f"\nЗагружаем сезон {year_to_load}: {start_date_of_season} → {end_date_of_season}")

            block_start_date = start_date_of_season
            while block_start_date <= end_date_of_season:
                block_end_date = min(block_start_date + timedelta(days=91), end_date_of_season)
                self.stdout.write(f"  Загрузка блока с {block_start_date} по {block_end_date}...")

                try:
                    rows_fetched_from_api = self.fetch_block_of_data(
                        latitude_of_city,
                        longitude_of_city,
                        city_name,
                        block_start_date,
                        block_end_date,
                        list_of_all_pollen_types
                    )
                    self.stdout.write(f"    Получено {len(rows_fetched_from_api)} почасовых записей")
                    list_of_rows_from_api.extend(rows_fetched_from_api)
                except Exception as exception_raised:
                    self.stdout.write(self.style.ERROR(f"Ошибка загрузки блока: {exception_raised}"))

                block_start_date = block_end_date + timedelta(days=1)
                time.sleep(1.2)

        number_of_records_created = self.aggregate_rows_and_save_to_database(
            list_of_rows_from_api,
            city_name,
            latitude_of_city,
            longitude_of_city
        )

        self.stdout.write(self.style.SUCCESS(f"\nЗагрузка завершена. Создано записей: {number_of_records_created}"))

    def fetch_block_of_data(self, latitude_of_city, longitude_of_city, city_name, start_date_of_block, end_date_of_block, list_of_all_pollen_types):
        api_url = "https://air-quality-api.open-meteo.com/v1/air-quality"

        api_parameters = {
            "latitude": latitude_of_city,
            "longitude": longitude_of_city,
            "hourly": [pollen_type.openmeteo_code for pollen_type in list_of_all_pollen_types],
            "start_date": start_date_of_block.isoformat(),
            "end_date": end_date_of_block.isoformat(),
            "timezone": "auto",
        }

        response_from_api = requests.get(api_url, params=api_parameters, timeout=30)
        response_from_api.raise_for_status()
        response_json_data = response_from_api.json()
        hourly_data_from_api = response_json_data.get("hourly", {})
        list_of_time_stamps = hourly_data_from_api.get("time", [])

        list_of_rows_to_return = []

        for index_of_time_stamp, time_stamp_string in enumerate(list_of_time_stamps):
            datetime_of_measurement = datetime.fromisoformat(time_stamp_string.replace("Z", "+00:00"))

            for pollen_type_instance in list_of_all_pollen_types:
                list_of_hourly_values_for_pollen_type = hourly_data_from_api.get(pollen_type_instance.openmeteo_code)
                if not list_of_hourly_values_for_pollen_type or list_of_hourly_values_for_pollen_type[index_of_time_stamp] is None:
                    continue

                concentration_value_for_this_hour = list_of_hourly_values_for_pollen_type[index_of_time_stamp]

                list_of_rows_to_return.append({
                    "datetime_of_measurement": datetime_of_measurement,
                    "pollen_type_id": pollen_type_instance.id,
                    "pollen_type_instance": pollen_type_instance,
                    "concentration_value": concentration_value_for_this_hour,
                })

        return list_of_rows_to_return

    def aggregate_rows_and_save_to_database(self, list_of_rows, city_name, latitude_of_city, longitude_of_city):
        if not list_of_rows:
            return 0

        dataframe_of_rows = pd.DataFrame(list_of_rows)
        dataframe_of_rows["datetime_of_measurement"] = pd.to_datetime(dataframe_of_rows["datetime_of_measurement"])
        dataframe_of_rows["year_of_measurement"] = dataframe_of_rows["datetime_of_measurement"].dt.year
        dataframe_of_rows["month_of_measurement"] = dataframe_of_rows["datetime_of_measurement"].dt.month
        dataframe_of_rows["day_of_measurement"] = dataframe_of_rows["datetime_of_measurement"].dt.day

        dataframe_of_rows = dataframe_of_rows[~((dataframe_of_rows["month_of_measurement"] == 2) & (dataframe_of_rows["day_of_measurement"] == 29))]

        dataframe_daily_by_year = (
            dataframe_of_rows
            .groupby(["year_of_measurement", "month_of_measurement", "day_of_measurement", "pollen_type_id"])
            .agg({
                "concentration_value": "mean",
                "pollen_type_instance": "first",
            })
            .reset_index()
        )

        dataframe_climatology_by_day = (
            dataframe_daily_by_year
            .groupby(["month_of_measurement", "day_of_measurement", "pollen_type_id"])
            .agg({
                "concentration_value": "mean",
                "pollen_type_instance": "first",
            })
            .reset_index()
        )

        list_of_objects_to_create = []

        for index, row_in_climatology in dataframe_climatology_by_day.iterrows():
            list_of_objects_to_create.append(
                PollenData(
                    pollen_type=row_in_climatology["pollen_type_instance"],
                    city=city_name,
                    latitude=latitude_of_city,
                    longitude=longitude_of_city,
                    date=date(2000, int(row_in_climatology["month_of_measurement"]), int(row_in_climatology["day_of_measurement"])),
                    hour=None,
                    concentration=float(row_in_climatology["concentration_value"]),
                )
            )

        PollenData.objects.bulk_create(list_of_objects_to_create, ignore_conflicts=True)

        return len(list_of_objects_to_create)