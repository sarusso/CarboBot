from django.contrib import admin
from django.urls import path
from django.views.generic.base import RedirectView
from .core import views, api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.chat, name='root'), # views.entrypoint
    path('main/', views.main, name='main'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('account/', views.user_account, name='account'),
    path('food/', views.food, name='food'),
    path('food_add/', views.food_add, name='food_add'),
    path('food_load/', views.food_load, name='food_load'),
    path('food_observations/', views.food_observations, name='food_observations'),
    path('food_observations_add/', views.food_observations_add, name='food_observations_add'),
    path('analytics/', views.analytics, name='analytics'),
    path('chat/', views.chat, name='chat'),
    path('api/v1/telegram', api.TelegramAPI.as_view(), name='telegram_api'),
]
