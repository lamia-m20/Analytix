"""
URL configuration for Analytix project.

The `urlpatterns` list routes URLs to views.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # لوحة التحكم
    path('admin/', admin.site.urls),

    # الصفحة الرئيسية
    path('', include('dashboards.urls')),

    # المستخدمون
    path('accounts/', include('accounts.urls')),

    # ملفات البيانات
    path('datasets/', include('datasets.urls')),

    # التحليلات
    path('analysis/', include('analysis.urls')),

    # التقارير
    path('reports/', include('reports.urls')),
]