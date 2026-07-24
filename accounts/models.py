from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    ACCOUNT_TYPES = [
        ('individual', 'فرد'),
        ('analyst', 'محلل بيانات'),
        ('company', 'شركة'),
        ('manager', 'مدير مؤسسة'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='المستخدم',
    )

    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPES,
        default='individual',
        verbose_name='نوع الحساب',
    )

    company_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='اسم الشركة أو المؤسسة',
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name='رقم الهاتف',
    )

    profile_image = models.ImageField(
        upload_to='accounts/profile_images/',
        blank=True,
        null=True,
        verbose_name='الصورة الشخصية',
    )

    max_file_size_mb = models.PositiveIntegerField(
        default=10,
        verbose_name='الحد الأقصى لحجم الملف بالميجابايت',
    )

    monthly_analysis_limit = models.PositiveIntegerField(
        default=20,
        verbose_name='الحد الشهري لعمليات التحليل',
    )

    analyses_used_this_month = models.PositiveIntegerField(
        default=0,
        verbose_name='التحليلات المستخدمة هذا الشهر',
    )

    is_verified = models.BooleanField(
        default=False,
        verbose_name='الحساب موثق',
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاريخ إنشاء الملف الشخصي',
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='تاريخ آخر تحديث',
    )

    class Meta:
        verbose_name = 'ملف المستخدم'
        verbose_name_plural = 'ملفات المستخدمين'
        ordering = ['-created_at']

    def __str__(self):
        return self.user.get_full_name() or self.user.username

    @property
    def remaining_analyses(self):
        remaining = (
            self.monthly_analysis_limit
            - self.analyses_used_this_month
        )
        return max(remaining, 0)
