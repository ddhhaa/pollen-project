from django.core.management.base import BaseCommand
from app.open_meteo import fetch_pollen_data
from app.models import UserProfile

class Command(BaseCommand):
    help = "Update pollen data from Open-Meteo"

    def handle(self, *args, **options):
        cities = [
            {"name": "Москва", "lat": 55.7558, "lon": 37.6176},
            {"name": "Санкт-Петербург", "lat": 59.9343, "lon": 30.3351},
            {"name": "Нижний Новгород", "lat": 56.3269, "lon": 44.0065},
            {"name": "Калининград", "lat": 54.7104, "lon": 20.4522},
            {"name": "Париж", "lat": 48.8566, "lon": 2.3522},
            {"name": "Лондон", "lat": 51.5074, "lon": -0.1278},
            {"name": "Нью-Йорк", "lat": 40.7128, "lon": -74.0060},
        ]
        for city_data in cities:  # <-- Изменено здесь
            city_name = city_data["name"]
            lat = city_data["lat"]
            lon = city_data["lon"]
            
            self.stdout.write(f"Обновление данных для города: {city_name}")
            try:
                fetch_pollen_data(
                    latitude=lat,
                    longitude=lon,
                    city=city_name
                )
                self.stdout.write(self.style.SUCCESS(f"Данные для {city_name} обновлены"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Ошибка для города {city_name}: {e}"))
        
        self.stdout.write(self.style.SUCCESS("Pollen data updated"))
