from django.contrib import admin

from .models import AnalysisConfiguration
from .models import AnalysisJob
from .models import AnalysisResult
from .models import DataCleaningOperation


class AnalysisConfigurationInline(
    admin.StackedInline
):
    model = AnalysisConfiguration
    extra = 0


class DataCleaningOperationInline(
    admin.TabularInline
):
    model = DataCleaningOperation
    extra = 0


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
    )

    search_fields = (
        'name',
        'owner__username',
        'dataset__title',
        'sheet__name',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    inlines = [
        AnalysisConfigurationInline,
        DataCleaningOperationInline,
    ]


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
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )