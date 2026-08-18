from django.urls import path

from . import views


app_name = 'dashboards'


urlpatterns = [
    path('', views.home, name='home'),
    path('dashboards/', views.dashboard_list, name='list'),
]
