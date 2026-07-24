from django.conf import settings
from django.db import models

from analysis.models import AnalysisResult


class Dashboard(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dashboards',
        verbose_name='صاحب لوحة المعلومات',
    )

    name = models.CharField(
        max_length=255,
        verbose_name='اسم لوحة المعلومات',
    )

    description = models.TextField(
        blank=True,
        verbose_name='الوصف',
    )

    is_public = models.BooleanField(
        default=False,
        verbose_name='لوحة عامة',
    )

    is_default = models.BooleanField(
        default=False,
        verbose_name='اللوحة الافتراضية',
    )

    layout_settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='إعدادات التصميم',
    )

    filters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='مرشحات اللوحة',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ آخر تحديث',
    )

    class Meta:
        verbose_name = 'لوحة معلومات'
        verbose_name_plural = 'لوحات المعلومات'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'is_public']),
        ]

    def __str__(self):
        return self.name


class DashboardWidget(models.Model):
    WIDGET_TYPES = [
        ('metric', 'بطاقة رقمية'),
        ('table', 'جدول'),
        ('bar', 'مخطط أعمدة'),
        ('line', 'مخطط خطي'),
        ('pie', 'مخطط دائري'),
        ('area', 'مخطط مساحي'),
        ('scatter', 'مخطط انتشار'),
        ('histogram', 'مدرج تكراري'),
        ('heatmap', 'خريطة حرارية'),
        ('text', 'نص'),
    ]

    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='widgets',
        verbose_name='لوحة المعلومات',
    )

    analysis_result = models.ForeignKey(
        AnalysisResult,
        on_delete=models.SET_NULL,
        related_name='dashboard_widgets',
        blank=True,
        null=True,
        verbose_name='نتيجة التحليل',
    )

    title = models.CharField(
        max_length=255,
        verbose_name='عنوان العنصر',
    )

    widget_type = models.CharField(
        max_length=30,
        choices=WIDGET_TYPES,
        verbose_name='نوع العنصر',
    )

    x_column = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='عمود المحور الأفقي',
    )

    y_column = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='عمود المحور الرأسي',
    )

    aggregation = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='طريقة التجميع',
    )

    position_x = models.PositiveIntegerField(
        default=0,
        verbose_name='الموقع الأفقي',
    )

    position_y = models.PositiveIntegerField(
        default=0,
        verbose_name='الموقع الرأسي',
    )

    width = models.PositiveIntegerField(
        default=6,
        verbose_name='العرض',
    )

    height = models.PositiveIntegerField(
        default=4,
        verbose_name='الارتفاع',
    )

    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتيب العرض',
    )

    settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='إعدادات العنصر',
    )

    is_visible = models.BooleanField(
        default=True,
        verbose_name='ظاهر',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإضافة',
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ التحديث',
    )

    class Meta:
        verbose_name = 'عنصر لوحة معلومات'
        verbose_name_plural = 'عناصر لوحات المعلومات'
        ordering = ['display_order', 'position_y', 'position_x']

    def __str__(self):
        return f'{self.dashboard.name} - {self.title}'


class DashboardShare(models.Model):
    PERMISSION_CHOICES = [
        ('view', 'عرض فقط'),
        ('edit', 'عرض وتعديل'),
    ]

    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        related_name='shares',
        verbose_name='لوحة المعلومات',
    )

    shared_with = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='shared_dashboards',
        verbose_name='مشاركة مع',
    )

    permission = models.CharField(
        max_length=10,
        choices=PERMISSION_CHOICES,
        default='view',
        verbose_name='الصلاحية',
    )

    shared_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ المشاركة',
    )

    class Meta:
        verbose_name = 'مشاركة لوحة'
        verbose_name_plural = 'مشاركات اللوحات'
        constraints = [
            models.UniqueConstraint(
                fields=['dashboard', 'shared_with'],
                name='unique_dashboard_share_per_user',
            )
        ]

    def __str__(self):
        return (
            f'{self.dashboard.name} مع '
            f'{self.shared_with.username}'
        )