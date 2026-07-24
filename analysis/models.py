from django.conf import settings
from django.db import models

from datasets.models import Dataset, DatasetSheet


class AnalysisJob(models.Model):
    ANALYSIS_TYPES = [
        ('descriptive', 'تحليل وصفي'),
        ('data_quality', 'تحليل جودة البيانات'),
        ('sales', 'تحليل المبيعات'),
        ('financial', 'تحليل مالي'),
        ('correlation', 'تحليل الارتباط'),
        ('comparison', 'تحليل المقارنة'),
        ('custom', 'تحليل مخصص'),
    ]

    STATUS_CHOICES = [
        ('new', 'جديد'),
        ('queued', 'في قائمة الانتظار'),
        ('processing', 'قيد التنفيذ'),
        ('completed', 'مكتمل'),
        ('failed', 'فشل'),
        ('cancelled', 'ملغي'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='analysis_jobs',
        verbose_name='صاحب التحليل',
    )

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='analysis_jobs',
        verbose_name='ملف البيانات',
    )

    sheet = models.ForeignKey(
        DatasetSheet,
        on_delete=models.CASCADE,
        related_name='analysis_jobs',
        verbose_name='ورقة العمل',
    )

    name = models.CharField(
        max_length=255,
        verbose_name='اسم التحليل',
    )

    analysis_type = models.CharField(
        max_length=30,
        choices=ANALYSIS_TYPES,
        default='descriptive',
        verbose_name='نوع التحليل',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True,
        verbose_name='حالة التحليل',
    )

    progress = models.PositiveSmallIntegerField(
        default=0,
        verbose_name='نسبة التقدم',
        help_text='قيمة من 0 إلى 100',
    )

    error_message = models.TextField(
        blank=True,
        verbose_name='رسالة الخطأ',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإنشاء',
    )

    started_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='وقت بدء التنفيذ',
    )

    completed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='وقت اكتمال التنفيذ',
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ آخر تحديث',
    )

    class Meta:
        verbose_name = 'عملية تحليل'
        verbose_name_plural = 'عمليات التحليل'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['analysis_type']),
        ]

    def __str__(self):
        return self.name


class AnalysisConfiguration(models.Model):
    MISSING_VALUES_METHODS = [
        ('none', 'دون تغيير'),
        ('drop_rows', 'حذف الصفوف الفارغة'),
        ('drop_columns', 'حذف الأعمدة الفارغة'),
        ('fill_zero', 'التعبئة بالصفر'),
        ('fill_mean', 'التعبئة بالمتوسط'),
        ('fill_median', 'التعبئة بالوسيط'),
        ('fill_mode', 'التعبئة بالقيمة الأكثر تكرارًا'),
        ('custom', 'قيمة مخصصة'),
    ]

    analysis_job = models.OneToOneField(
        AnalysisJob,
        on_delete=models.CASCADE,
        related_name='configuration',
        verbose_name='عملية التحليل',
    )

    selected_columns = models.JSONField(
        default=list,
        blank=True,
        verbose_name='الأعمدة المحددة',
    )

    group_by_columns = models.JSONField(
        default=list,
        blank=True,
        verbose_name='أعمدة التجميع',
    )

    value_columns = models.JSONField(
        default=list,
        blank=True,
        verbose_name='أعمدة القيم',
    )

    date_column = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='عمود التاريخ',
    )

    missing_values_method = models.CharField(
        max_length=30,
        choices=MISSING_VALUES_METHODS,
        default='none',
        verbose_name='طريقة معالجة القيم الفارغة',
    )

    custom_fill_value = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='قيمة التعبئة المخصصة',
    )

    remove_duplicates = models.BooleanField(
        default=False,
        verbose_name='حذف الصفوف المكررة',
    )

    remove_outliers = models.BooleanField(
        default=False,
        verbose_name='إزالة القيم الشاذة',
    )

    filters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='المرشحات',
    )

    sorting = models.JSONField(
        default=list,
        blank=True,
        verbose_name='إعدادات الترتيب',
    )

    additional_options = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='إعدادات إضافية',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ إنشاء الإعدادات',
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ تحديث الإعدادات',
    )

    class Meta:
        verbose_name = 'إعدادات التحليل'
        verbose_name_plural = 'إعدادات التحليلات'

    def __str__(self):
        return f'إعدادات: {self.analysis_job.name}'


class DataCleaningOperation(models.Model):
    OPERATION_TYPES = [
        ('drop_missing', 'حذف القيم الفارغة'),
        ('fill_missing', 'تعبئة القيم الفارغة'),
        ('remove_duplicates', 'حذف التكرارات'),
        ('rename_column', 'إعادة تسمية عمود'),
        ('drop_column', 'حذف عمود'),
        ('replace_value', 'استبدال قيمة'),
        ('change_type', 'تغيير نوع البيانات'),
        ('format_date', 'تنسيق التاريخ'),
        ('remove_outliers', 'إزالة القيم الشاذة'),
        ('trim_text', 'تنظيف النصوص'),
    ]

    analysis_job = models.ForeignKey(
        AnalysisJob,
        on_delete=models.CASCADE,
        related_name='cleaning_operations',
        verbose_name='عملية التحليل',
    )

    operation_type = models.CharField(
        max_length=30,
        choices=OPERATION_TYPES,
        verbose_name='نوع عملية التنظيف',
    )

    column_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='اسم العمود',
    )

    parameters = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='معاملات العملية',
    )

    operation_order = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتيب التنفيذ',
    )

    is_enabled = models.BooleanField(
        default=True,
        verbose_name='مفعلة',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإضافة',
    )

    class Meta:
        verbose_name = 'عملية تنظيف'
        verbose_name_plural = 'عمليات تنظيف البيانات'
        ordering = ['operation_order']

    def __str__(self):
        return (
            f'{self.get_operation_type_display()} '
            f'- {self.analysis_job.name}'
        )


class AnalysisResult(models.Model):
    analysis_job = models.OneToOneField(
        AnalysisJob,
        on_delete=models.CASCADE,
        related_name='result',
        verbose_name='عملية التحليل',
    )

    summary = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='ملخص النتائج',
    )

    statistics = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='النتائج الإحصائية',
    )

    table_data = models.JSONField(
        default=list,
        blank=True,
        verbose_name='بيانات الجدول',
    )

    chart_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='بيانات الرسوم البيانية',
    )

    insights = models.JSONField(
        default=list,
        blank=True,
        verbose_name='الاستنتاجات',
    )

    rows_before_cleaning = models.PositiveBigIntegerField(
        default=0,
        verbose_name='عدد الصفوف قبل التنظيف',
    )

    rows_after_cleaning = models.PositiveBigIntegerField(
        default=0,
        verbose_name='عدد الصفوف بعد التنظيف',
    )

    processed_file = models.FileField(
        upload_to='analysis/processed/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='الملف المعالج',
    )

    execution_time_seconds = models.FloatField(
        default=0,
        verbose_name='مدة التنفيذ بالثواني',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ حفظ النتيجة',
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ تحديث النتيجة',
    )

    class Meta:
        verbose_name = 'نتيجة تحليل'
        verbose_name_plural = 'نتائج التحليلات'
        ordering = ['-created_at']

    def __str__(self):
        return f'نتيجة: {self.analysis_job.name}'