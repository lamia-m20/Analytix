from django.contrib import admin

from .models import Report, ReportFile


class ReportFileInline(admin.TabularInline):
    model = ReportFile
    extra = 0

    fields = (
        'filename',
        'file',
        'file_size',
        'downloads_count',
        'expires_at',
        'created_at',
    )

    readonly_fields = (
        'file_size',
        'downloads_count',
        'created_at',
    )

    show_change_link = True


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'owner',
        'report_type',
        'file_format',
        'status',
        'created_at',
        'completed_at',
    )

    list_filter = (
        'report_type',
        'file_format',
        'status',
        'include_summary',
        'include_tables',
        'include_charts',
        'created_at',
    )

    search_fields = (
        'title',
        'owner__username',
        'owner__email',
        'analysis_result__analysis_job__name',
        'dashboard__name',
    )

    readonly_fields = (
        'created_at',
        'completed_at',
    )

    fieldsets = (
        (
            'بيانات التقرير',
            {
                'fields': (
                    'owner',
                    'title',
                    'report_type',
                    'file_format',
                )
            },
        ),
        (
            'مصدر التقرير',
            {
                'fields': (
                    'analysis_result',
                    'dashboard',
                )
            },
        ),
        (
            'محتوى التقرير',
            {
                'fields': (
                    'include_summary',
                    'include_tables',
                    'include_charts',
                    'report_settings',
                )
            },
        ),
        (
            'حالة الإنشاء',
            {
                'fields': (
                    'status',
                    'error_message',
                )
            },
        ),
        (
            'التواريخ',
            {
                'fields': (
                    'created_at',
                    'completed_at',
                )
            },
        ),
    )

    inlines = [
        ReportFileInline,
    ]


@admin.register(ReportFile)
class ReportFileAdmin(admin.ModelAdmin):
    list_display = (
        'filename',
        'report',
        'file_size',
        'downloads_count',
        'expires_at',
        'created_at',
    )

    list_filter = (
        'created_at',
        'expires_at',
    )

    search_fields = (
        'filename',
        'report__title',
        'report__owner__username',
    )

    readonly_fields = (
        'file_size',
        'downloads_count',
        'created_at',
    )

    fieldsets = (
        (
            'بيانات الملف',
            {
                'fields': (
                    'report',
                    'filename',
                    'file',
                    'file_size',
                )
            },
        ),
        (
            'معلومات التحميل',
            {
                'fields': (
                    'downloads_count',
                    'expires_at',
                )
            },
        ),
        (
            'التاريخ',
            {
                'fields': (
                    'created_at',
                )
            },
        ),
    )