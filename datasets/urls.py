from django.urls import path

from . import views


app_name = 'datasets'


urlpatterns = [
    path(
        'my-analyses/',
        views.my_analyses,
        name='my_analyses',
    ),
    path('history/', views.dataset_history, name='history'),
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
        '<int:dataset_id>/dashboard/edit/',
        views.edit_dashboard,
        name='edit_dashboard',
    ),
    path('<int:dataset_id>/export/excel/', views.export_excel, name='export_excel'),
    path('<int:dataset_id>/export/csv/', views.export_csv, name='export_csv'),
    path('<int:dataset_id>/export/pdf/', views.export_pdf, name='export_pdf'),
    path('<int:dataset_id>/export/powerpoint/', views.export_powerpoint, name='export_powerpoint'),

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
