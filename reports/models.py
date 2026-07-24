from django.conf import settings
from django.db import models

from analysis.models import AnalysisResult
from dashboards.models import Dashboard


class Report(models.Model):
    REPORT_TYPES = [
        ('analysis', 'تقرير تحليل بيانات'),
        ('data_quality', 'تقرير جودة البيانات'),
        ('sales', 'تقرير مبيعات'),
        ('financial', 'تقرير مالي'),
        ('comparison', 'تقرير مقارنة'),
        ('executive', 'تقرير تنفيذي'),
        ('cleaned_data', 'ملف بيانات منظف'),
    ]

    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('xlsx', 'Excel XLSX'),
        ('csv', 'CSV'),
    ]

    STATUS_CHOICES = [
        ('new', 'جديد'),
        ('queued', 'في قائمة الانتظار'),
        ('generating', 'جارٍ الإنشاء'),
        ('completed', 'مكتمل'),
        ('failed', 'فشل'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='صاحب التقرير',
    )

    analysis_result = models.ForeignKey(
        AnalysisResult,
        on_delete=models.SET_NULL,
        related_name='reports',
        blank=True,
        null=True,
        verbose_name='نتيجة التحليل',
    )

    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.SET_NULL,
        related_name='reports',
        blank=True,
        null=True,
        verbose_name='لوحة المعلومات',
    )

    title = models.CharField(
        max_length=255,
        verbose_name='عنوان التقرير',
    )

    report_type = models.CharField(
        max_length=30,
        choices=REPORT_TYPES,
        default='analysis',
        verbose_name='نوع التقرير',
    )

    file_format = models.CharField(
        max_length=10,
        choices=FORMAT_CHOICES,
        default='pdf',
        verbose_name='صيغة التقرير',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True,
        verbose_name='حالة التقرير',
    )

    include_summary = models.BooleanField(
        default=True,
        verbose_name='تضمين الملخص',
    )

    include_tables = models.BooleanField(
        default=True,
        verbose_name='تضمين الجداول',
    )

    include_charts = models.BooleanField(
        default=True,
        verbose_name='تضمين الرسوم البيانية',
    )

    report_settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='إعدادات التقرير',
    )

    error_message = models.TextField(
        blank=True,
        verbose_name='رسالة الخطأ',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الطلب',
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='تاريخ اكتمال التقرير',
    )

    class Meta:
        verbose_name = 'تقرير'
        verbose_name_plural = 'التقارير'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['report_type']),
        ]

    def __str__(self):
        return self.title


class ReportFile(models.Model):
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='files',
        verbose_name='التقرير',
    )

    file = models.FileField(
        upload_to='reports/generated/%Y/%m/',
        verbose_name='ملف التقرير',
    )

    filename = models.CharField(
        max_length=255,
        verbose_name='اسم الملف',
    )

    file_size = models.PositiveBigIntegerField(
        default=0,
        verbose_name='حجم الملف بالبايت',
    )

    downloads_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد مرات التحميل',
    )

    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='تاريخ انتهاء الملف',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ إنشاء الملف',
    )

    class Meta:
        verbose_name = 'ملف تقرير'
        verbose_name_plural = 'ملفات التقارير'
        ordering = ['-created_at']

    def __str__(self):
        return self.filename

    def save(self, *args, **kwargs):
        if self.file:
            if not self.filename:
                self.filename = self.file.name.split('/')[-1]

            try:
                self.file_size = self.file.size
            except (AttributeError, OSError):
                pass

        super().save(*args, **kwargs)