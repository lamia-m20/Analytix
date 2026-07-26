from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # لوحة الإدارة
    path('lamia/', admin.site.urls),

    # الصفحة الرئيسية
    path('', include('dashboards.urls')),

    # الحسابات
    path('accounts/', include('accounts.urls')),

    # رفع وتحليل الملفات
    path('datasets/', include('datasets.urls')),

    # التحليلات
    path('analysis/', include('analysis.urls')),

    # التقارير
    path('reports/', include('reports.urls')),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )