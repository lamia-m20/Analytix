from django.contrib import admin

from .models import Dataset
from .models import DatasetColumn
from .models import DatasetSheet


class DatasetSheetInline(admin.TabularInline):
    model = DatasetSheet

    extra = 0

    fields = (
        'name',
        'index',
        'row_count',
        'column_count',
        'is_active',
    )

    readonly_fields = (
        'name',
        'index',
        'row_count',
        'column_count',
    )


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'status',
        'file_size_mb',
        'uploaded_at',
    )

    list_filter = (
        'status',
        'uploaded_at',
    )

    search_fields = (
        'title',
        'original_filename',
        'user__username',
        'user__email',
    )

    readonly_fields = (
        'original_filename',
        'file_size',
        'uploaded_at',
        'updated_at',
    )

    inlines = [
        DatasetSheetInline,
    ]


@admin.register(DatasetSheet)
class DatasetSheetAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'dataset',
        'index',
        'row_count',
        'column_count',
        'is_active',
    )

    list_filter = (
        'is_active',
    )

    search_fields = (
        'name',
        'dataset__title',
    )


@admin.register(DatasetColumn)
class DatasetColumnAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'sheet',
        'position',
        'data_type',
        'null_count',
        'unique_count',
    )

    search_fields = (
        'name',
        'sheet__name',
        'sheet__dataset__title',
    )