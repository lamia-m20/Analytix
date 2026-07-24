from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'account_type',
        'company_name',
        'phone',
        'is_verified',
        'monthly_analysis_limit',
        'analyses_used_this_month',
        'created_at',
    )

    list_filter = (
        'account_type',
        'is_verified',
        'created_at',
    )

    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
        'company_name',
        'phone',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'remaining_analyses',
    )

    fieldsets = (
        (
            'بيانات المستخدم',
            {
                'fields': (
                    'user',
                    'account_type',
                    'company_name',
                    'phone',
                    'profile_image',
                )
            },
        ),
        (
            'حدود الاستخدام',
            {
                'fields': (
                    'max_file_size_mb',
                    'monthly_analysis_limit',
                    'analyses_used_this_month',
                    'remaining_analyses',
                )
            },
        ),
        (
            'حالة الحساب',
            {
                'fields': (
                    'is_verified',
                )
            },
        ),
        (
            'التواريخ',
            {
                'fields': (
                    'created_at',
                    'updated_at',
                )
            },
        ),
    )