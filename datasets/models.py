from pathlib import Path

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models


class Dataset(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'تم الرفع'),
        ('validating', 'جارٍ التحقق'),
        ('ready', 'جاهز'),
        ('processing', 'قيد المعالجة'),
        ('processed', 'تمت المعالجة'),
        ('failed', 'فشل'),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='datasets',
        verbose_name='صاحب الملف',
    )

    name = models.CharField(
        max_length=255,
        verbose_name='اسم مجموعة البيانات',
    )

    original_file = models.FileField(
        upload_to='datasets/original/%Y/%m/',
        validators=[
            FileExtensionValidator(
                allowed_extensions=['xlsx', 'xls']
            )
        ],
        verbose_name='ملف Excel الأصلي',
    )

    original_filename = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='اسم الملف الأصلي',
    )

    file_size = models.PositiveBigIntegerField(
        default=0,
        verbose_name='حجم الملف بالبايت',
    )

    file_extension = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='امتداد الملف',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='uploaded',
        db_index=True,
        verbose_name='حالة الملف',
    )

    sheets_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد أوراق العمل',
    )

    selected_sheet_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='ورقة العمل المحددة',
    )

    error_message = models.TextField(
        blank=True,
        verbose_name='رسالة الخطأ',
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='نشط',
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الرفع',
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ آخر تحديث',
    )

    processed_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='تاريخ اكتمال المعالجة',
    )

    class Meta:
        verbose_name = 'ملف بيانات'
        verbose_name_plural = 'ملفات البيانات'
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['uploaded_at']),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.original_file:
            if not self.original_filename:
                self.original_filename = Path(
                    self.original_file.name
                ).name

            self.file_extension = Path(
                self.original_file.name
            ).suffix.lower().replace('.', '')

            try:
                self.file_size = self.original_file.size
            except (AttributeError, OSError):
                pass

        super().save(*args, **kwargs)


class DatasetSheet(models.Model):
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='sheets',
        verbose_name='ملف البيانات',
    )

    name = models.CharField(
        max_length=255,
        verbose_name='اسم ورقة العمل',
    )

    sheet_index = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتيب ورقة العمل',
    )

    rows_count = models.PositiveBigIntegerField(
        default=0,
        verbose_name='عدد الصفوف',
    )

    columns_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد الأعمدة',
    )

    empty_cells_count = models.PositiveBigIntegerField(
        default=0,
        verbose_name='عدد الخلايا الفارغة',
    )

    duplicate_rows_count = models.PositiveBigIntegerField(
        default=0,
        verbose_name='عدد الصفوف المكررة',
    )

    preview_data = models.JSONField(
        default=list,
        blank=True,
        verbose_name='معاينة البيانات',
    )

    is_selected = models.BooleanField(
        default=False,
        verbose_name='ورقة العمل محددة',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإضافة',
    )

    class Meta:
        verbose_name = 'ورقة عمل'
        verbose_name_plural = 'أوراق العمل'
        ordering = ['sheet_index']
        constraints = [
            models.UniqueConstraint(
                fields=['dataset', 'name'],
                name='unique_sheet_name_per_dataset',
            )
        ]

    def __str__(self):
        return f'{self.dataset.name} - {self.name}'


class DatasetColumn(models.Model):
    DATA_TYPE_CHOICES = [
        ('text', 'نص'),
        ('integer', 'عدد صحيح'),
        ('float', 'عدد عشري'),
        ('boolean', 'قيمة منطقية'),
        ('date', 'تاريخ'),
        ('datetime', 'تاريخ ووقت'),
        ('category', 'تصنيف'),
        ('unknown', 'غير معروف'),
    ]

    sheet = models.ForeignKey(
        DatasetSheet,
        on_delete=models.CASCADE,
        related_name='columns',
        verbose_name='ورقة العمل',
    )

    name = models.CharField(
        max_length=255,
        verbose_name='اسم العمود',
    )

    original_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='اسم العمود الأصلي',
    )

    column_index = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتيب العمود',
    )

    detected_type = models.CharField(
        max_length=20,
        choices=DATA_TYPE_CHOICES,
        default='unknown',
        verbose_name='نوع البيانات المكتشف',
    )

    missing_values_count = models.PositiveBigIntegerField(
        default=0,
        verbose_name='عدد القيم الفارغة',
    )

    unique_values_count = models.PositiveBigIntegerField(
        default=0,
        verbose_name='عدد القيم الفريدة',
    )

    minimum_value = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='أقل قيمة',
    )

    maximum_value = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='أعلى قيمة',
    )

    mean_value = models.FloatField(
        blank=True,
        null=True,
        verbose_name='المتوسط',
    )

    median_value = models.FloatField(
        blank=True,
        null=True,
        verbose_name='الوسيط',
    )

    standard_deviation = models.FloatField(
        blank=True,
        null=True,
        verbose_name='الانحراف المعياري',
    )

    sample_values = models.JSONField(
        default=list,
        blank=True,
        verbose_name='عينات من القيم',
    )

    is_numeric = models.BooleanField(
        default=False,
        verbose_name='عمود رقمي',
    )

    is_date = models.BooleanField(
        default=False,
        verbose_name='عمود تاريخ',
    )

    class Meta:
        verbose_name = 'عمود بيانات'
        verbose_name_plural = 'أعمدة البيانات'
        ordering = ['column_index']
        constraints = [
            models.UniqueConstraint(
                fields=['sheet', 'name'],
                name='unique_column_name_per_sheet',
            )
        ]

    def __str__(self):
        return f'{self.sheet.name} - {self.name}'