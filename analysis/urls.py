from django.urls import path

from . import views

app_name = 'analysis'

urlpatterns = [
    path('', views.analysis_list, name='list'),
]
