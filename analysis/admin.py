from django.contrib import admin

from .models import (
    AnalysisConfiguration,
    AnalysisJob,
    AnalysisResult,
    DataCleaningOperation,
)


class AnalysisConfigurationInline(admin.StackedInline):
    model = AnalysisConfiguration
    extra = 0
    max_num = 1

    fields = (
        'selected_columns',
        'group_by_columns',
        'value_columns',
        'date_column',
        'missing_values_method',
        'remove_duplicates',
        'remove_outliers',
    )

    show_change_link = True


class DataCleaningOperationInline(admin.TabularInline):
    model = DataCleaningOperation
    extra = 0

    fields = (
        'operation_type',
        'column_name',
        'operation_order',
        'is_enabled',
    )

    show_change_link = True


class AnalysisResultInline(admin.StackedInline):
    model = AnalysisResult
    extra = 0
    max_num = 1

    fields = (
        'rows_before_cleaning',
        'rows_after_cleaning',
        'execution_time_seconds',
        'processed_file',
        'created_at',
    )

    readonly_fields = (
        'created_at',
    )

    show_change_link = True


@admin.register(AnalysisJob)
class AnalysisJobAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'owner',
        'dataset',
        'sheet',
        'analysis_type',
        'status',
        'progress',
        'created_at',
    )

    list_filter = (
        'analysis_type',
        'status',
        'created_at',
        'completed_at',
    )

    search_fields = (
        'name',
        'owner__username',
        'owner__email',
        'dataset__name',
        'sheet__name',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'started_at',
        'completed_at',
    )

    fieldsets = (
        (
            'بيانات التحليل',
            {
                'fields': (
                    'owner',
                    'dataset',
                    'sheet',
                    'name',
                    'analysis_type',
                )
            },
        ),
        (
            'حالة التنفيذ',
            {
                'fields': (
                    'status',
                    'progress',
                    'error_message',
                )
            },
        ),
        (
            'التواريخ',
            {
                'fields': (
                    'created_at',
                    'started_at',
                    'completed_at',
                    'updated_at',
                )
            },
        ),
    )

    inlines = [
        AnalysisConfigurationInline,
        DataCleaningOperationInline,
        AnalysisResultInline,
    ]


@admin.register(AnalysisConfiguration)
class AnalysisConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        'analysis_job',
        'missing_values_method',
        'remove_duplicates',
        'remove_outliers',
        'created_at',
    )

    list_filter = (
        'missing_values_method',
        'remove_duplicates',
        'remove_outliers',
    )

    search_fields = (
        'analysis_job__name',
        'analysis_job__owner__username',
        'date_column',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )


@admin.register(DataCleaningOperation)
class DataCleaningOperationAdmin(admin.ModelAdmin):
    list_display = (
        'analysis_job',
        'operation_type',
        'column_name',
        'operation_order',
        'is_enabled',
        'created_at',
    )

    list_filter = (
        'operation_type',
        'is_enabled',
    )

    search_fields = (
        'analysis_job__name',
        'column_name',
    )

    ordering = (
        'analysis_job',
        'operation_order',
    )

    readonly_fields = (
        'created_at',
    )


@admin.register(AnalysisResult)
class AnalysisResultAdmin(admin.ModelAdmin):
    list_display = (
        'analysis_job',
        'rows_before_cleaning',
        'rows_after_cleaning',
        'execution_time_seconds',
        'created_at',
    )

    search_fields = (
        'analysis_job__name',
        'analysis_job__owner__username',
    )

    readonly_fields = (
        'summary',
        'statistics',
        'table_data',
        'chart_data',
        'insights',
        'rows_before_cleaning',
        'rows_after_cleaning',
        'execution_time_seconds',
        'created_at',
        'updated_at',
    )

    fieldsets = (
        (
            'عملية التحليل',
            {
                'fields': (
                    'analysis_job',
                    'processed_file',
                )
            },
        ),
        (
            'معلومات المعالجة',
            {
                'fields': (
                    'rows_before_cleaning',
                    'rows_after_cleaning',
                    'execution_time_seconds',
                )
            },
        ),
        (
            'نتائج التحليل',
            {
                'fields': (
                    'summary',
                    'statistics',
                    'table_data',
                    'chart_data',
                    'insights',
                ),
                'classes': (
                    'collapse',
                ),
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