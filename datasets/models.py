from pathlib import Path

from cloudinary_storage.storage import RawMediaCloudinaryStorage
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models


raw_storage = RawMediaCloudinaryStorage()


def validate_excel_size(uploaded_file):
    """
    حد احتياطي عام للملفات.

    الحد الخاص بكل مستخدم يتم التحقق منه
    داخل DatasetUploadForm.
    """

    default_limit_mb = 10
    maximum_bytes = default_limit_mb * 1024 * 1024

    if not uploaded_file:
        return

    if uploaded_file.size > maximum_bytes:
        raise ValidationError(
            f'حجم الملف أكبر من الحد العام المسموح، '
            f'وهو {default_limit_mb} ميجابايت.'
        )


class Dataset(models.Model):
    STATUS_CHOICES = [
        ('uploaded', 'تم الرفع'),
        ('reading', 'جارٍ قراءة الملف'),
        ('ready', 'جاهز للتحليل'),
        ('failed', 'فشل تجهيز الملف'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='datasets',
        verbose_name='المستخدم',
    )

    title = models.CharField(
        max_length=200,
        verbose_name='اسم ملف البيانات',
    )

    file = models.FileField(
        upload_to='analytix/excel_files/%Y/%m/',
        storage=raw_storage,
          max_length=500,
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    'xlsx',
                    'xls',
                    'xlsm',
                ],
            ),
            validate_excel_size,
        ],
        verbose_name='ملف Excel',
    )

    original_filename = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='اسم الملف الأصلي',
    )

    file_size = models.PositiveBigIntegerField(
        default=0,
        editable=False,
        verbose_name='حجم الملف بالبايت',
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='uploaded',
        db_index=True,
        verbose_name='حالة الملف',
    )

    error_message = models.TextField(
        blank=True,
        verbose_name='رسالة الخطأ',
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الرفع',
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ آخر تحديث',
    )

    class Meta:
        verbose_name = 'ملف بيانات'
        verbose_name_plural = 'ملفات البيانات'
        ordering = ['-uploaded_at']

        indexes = [
            models.Index(
                fields=['user', 'status'],
            ),
            models.Index(
                fields=['uploaded_at'],
            ),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.file and not self.original_filename:
            self.original_filename = Path(
                self.file.name
            ).name

        if (
            self.file
            and not getattr(
                self.file,
                '_committed',
                True,
            )
        ):
            self.file_size = self.file.size

        super().save(*args, **kwargs)

    @property
    def file_size_mb(self):
        return round(
            self.file_size / (1024 * 1024),
            2,
        )


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

    index = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتيب ورقة العمل',
    )

    row_count = models.PositiveBigIntegerField(
        default=0,
        verbose_name='عدد الصفوف',
    )

    column_count = models.PositiveIntegerField(
        default=0,
        verbose_name='عدد الأعمدة',
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='مفعلة',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ الإضافة',
    )

    class Meta:
        verbose_name = 'ورقة عمل'
        verbose_name_plural = 'أوراق العمل'
        ordering = ['index']

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'dataset',
                    'name',
                ],
                name='unique_sheet_name_per_dataset',
            ),
        ]

    def __str__(self):
        return (
            f'{self.dataset.title} - '
            f'{self.name}'
        )


class DatasetColumn(models.Model):
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

    position = models.PositiveIntegerField(
        default=0,
        verbose_name='ترتيب العمود',
    )

    data_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='نوع البيانات',
    )

    null_count = models.PositiveBigIntegerField(
        default=0,
        verbose_name='عدد القيم الفارغة',
    )

    unique_count = models.PositiveBigIntegerField(
        default=0,
        verbose_name='عدد القيم الفريدة',
    )

    sample_values = models.JSONField(
        default=list,
        blank=True,
        verbose_name='قيم نموذجية',
    )

    class Meta:
        verbose_name = 'عمود بيانات'
        verbose_name_plural = 'أعمدة البيانات'
        ordering = ['position']

        constraints = [
            models.UniqueConstraint(
                fields=[
                    'sheet',
                    'position',
                ],
                name='unique_column_position_per_sheet',
            ),
        ]

    def __str__(self):
        return (
            f'{self.sheet.name} - '
            f'{self.name}'
        )