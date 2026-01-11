from django.core.management.base import BaseCommand
from app.open_meteo import fetch_pollen_data


class Command(BaseCommand):
    help = "Update pollen data from Open-Meteo"

    def handle(self, *args, **options):
        fetch_pollen_data(
            latitude=55.7558,
            longitude=37.6176,
            city="Москва"
        )
        self.stdout.write(self.style.SUCCESS("Pollen data updated"))
