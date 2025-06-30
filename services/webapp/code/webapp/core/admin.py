from django.contrib import admin

from .models import Food, FoodObservation, SearchQuery

admin.site.register(Food)
admin.site.register(FoodObservation)
admin.site.register(SearchQuery)
