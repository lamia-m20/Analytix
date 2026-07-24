from django.contrib import admin

from .models import Dataset, DatasetColumn, DatasetSheet


class DatasetSheetInline(admin.TabularInline):
    model = DatasetSheet
    extra = 0

    fields = (
        'name',
        'sheet_index',
        'rows_count',
        'columns_count',
        'is_selected',
    )

    readonly_fields = (
        'rows_count',
        'columns_count',
    )

    show_change_link = True


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'owner',
        'original_filename',
        'status',
        'sheets_count',
        'file_size',
        'is_active',
        'uploaded_at',
    )

    list_filter = (
        'status',
        'is_active',
        'file_extension',
        'uploaded_at',
    )

    search_fields = (
        'name',
        'original_filename',
        'owner__username',
        'owner__email',
        'selected_sheet_name',
    )

    readonly_fields = (
        'original_filename',
        'file_size',
        'file_extension',
        'sheets_count',
        'uploaded_at',
        'updated_at',
        'processed_at',
    )

    fieldsets = (
        (
            'بيانات الملف',
            {
                'fields': (
                    'owner',
                    'name',
                    'original_file',
                    'original_filename',
                    'file_extension',
                    'file_size',
                )
            },
        ),
        (
            'معلومات المعالجة',
            {
                'fields': (
                    'status',
                    'sheets_count',
                    'selected_sheet_name',
                    'error_message',
                    'processed_at',
                )
            },
        ),
        (
            'الحالة والتواريخ',
            {
                'fields': (
                    'is_active',
                    'uploaded_at',
                    'updated_at',
                )
            },
        ),
    )

    inlines = [
        DatasetSheetInline,
    ]


class DatasetColumnInline(admin.TabularInline):
    model = DatasetColumn
    extra = 0

    fields = (
        'name',
        'column_index',
        'detected_type',
        'missing_values_count',
        'unique_values_count',
        'is_numeric',
        'is_date',
    )

    readonly_fields = (
        'missing_values_count',
        'unique_values_count',
    )

    show_change_link = True


@admin.register(DatasetSheet)
class DatasetSheetAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'dataset',
        'sheet_index',
        'rows_count',
        'columns_count',
        'duplicate_rows_count',
        'is_selected',
        'created_at',
    )

    list_filter = (
        'is_selected',
        'created_at',
    )

    search_fields = (
        'name',
        'dataset__name',
        'dataset__owner__username',
    )

    readonly_fields = (
        'rows_count',
        'columns_count',
        'empty_cells_count',
        'duplicate_rows_count',
        'preview_data',
        'created_at',
    )

    fieldsets = (
        (
            'ورقة العمل',
            {
                'fields': (
                    'dataset',
                    'name',
                    'sheet_index',
                    'is_selected',
                )
            },
        ),
        (
            'إحصاءات الورقة',
            {
                'fields': (
                    'rows_count',
                    'columns_count',
                    'empty_cells_count',
                    'duplicate_rows_count',
                )
            },
        ),
        (
            'معاينة البيانات',
            {
                'fields': (
                    'preview_data',
                ),
                'classes': (
                    'collapse',
                ),
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

    inlines = [
        DatasetColumnInline,
    ]


@admin.register(DatasetColumn)
class DatasetColumnAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'sheet',
        'column_index',
        'detected_type',
        'missing_values_count',
        'unique_values_count',
        'is_numeric',
        'is_date',
    )

    list_filter = (
        'detected_type',
        'is_numeric',
        'is_date',
    )

    search_fields = (
        'name',
        'original_name',
        'sheet__name',
        'sheet__dataset__name',
    )

    readonly_fields = (
        'missing_values_count',
        'unique_values_count',
        'minimum_value',
        'maximum_value',
        'mean_value',
        'median_value',
        'standard_deviation',
        'sample_values',
    )

    fieldsets = (
        (
            'معلومات العمود',
            {
                'fields': (
                    'sheet',
                    'name',
                    'original_name',
                    'column_index',
                    'detected_type',
                    'is_numeric',
                    'is_date',
                )
            },
        ),
        (
            'الإحصاءات',
            {
                'fields': (
                    'missing_values_count',
                    'unique_values_count',
                    'minimum_value',
                    'maximum_value',
                    'mean_value',
                    'median_value',
                    'standard_deviation',
                )
            },
        ),
        (
            'عينات القيم',
            {
                'fields': (
                    'sample_values',
                ),
                'classes': (
                    'collapse',
                ),
            },
        ),
    )