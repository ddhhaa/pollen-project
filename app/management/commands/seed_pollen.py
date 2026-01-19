from django.core.management.base import BaseCommand
from app.models import PollenType

class Command(BaseCommand):
    def handle(self, *args, **options):
        pollen_types = [
            {"name": "Берёза", "code": "birch_pollen", "category": "tree", "color": "#8BC34A"},
            {"name": "Ольха", "code": "alder_pollen", "category": "tree", "color": "#5970AA"},
            {"name": "Травы", "code": "grass_pollen", "category": "grass", "color": "#FF9800"},
            {"name": "Амброзия", "code": "ragweed_pollen", "category": "weed", "color": "#F44336"},
            {"name": "Полынь", "code": "mugwort_pollen", "category": "weed", "color": "#9C27B0"},
        ]
        
        for pt in pollen_types:
            PollenType.objects.get_or_create(
                name=pt["name"],
                defaults={
                    "openmeteo_code": pt["code"],
                    "category": pt["category"],
                    "color": pt["color"],
                    "allergenicity": 1.0
                }
            )