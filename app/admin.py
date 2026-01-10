from django.contrib import admin
from .models import PollenType, PollenData, UserProfile, UserAllergy, Recommendation

admin.site.register(PollenType)
admin.site.register(PollenData)
admin.site.register(UserProfile)
admin.site.register(UserAllergy)
admin.site.register(Recommendation)
