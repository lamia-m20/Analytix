from django.urls import path

from . import views


app_name = 'datasets'


urlpatterns = [
    path(
        '',
        views.dataset_list,
        name='list',
    ),

    path(
        'upload/',
        views.upload_dataset,
        name='upload',
    ),

    path(
        '<int:pk>/',
        views.dataset_detail,
        name='detail',
    ),

    path(
        '<int:pk>/delete/',
        views.delete_dataset,
        name='delete',
    ),
]