from django.contrib import admin

from .models import Dashboard, DashboardShare, DashboardWidget


class DashboardWidgetInline(admin.TabularInline):
    model = DashboardWidget
    extra = 0

    fields = (
        'title',
        'widget_type',
        'analysis_result',
        'display_order',
        'is_visible',
    )

    show_change_link = True


class DashboardShareInline(admin.TabularInline):
    model = DashboardShare
    extra = 0

    fields = (
        'shared_with',
        'permission',
        'shared_at',
    )

    readonly_fields = (
        'shared_at',
    )

    show_change_link = True


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'owner',
        'is_public',
        'is_default',
        'created_at',
        'updated_at',
    )

    list_filter = (
        'is_public',
        'is_default',
        'created_at',
    )

    search_fields = (
        'name',
        'description',
        'owner__username',
        'owner__email',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    fieldsets = (
        (
            'بيانات لوحة المعلومات',
            {
                'fields': (
                    'owner',
                    'name',
                    'description',
                )
            },
        ),
        (
            'إعدادات النشر',
            {
                'fields': (
                    'is_public',
                    'is_default',
                )
            },
        ),
        (
            'إعدادات التصميم',
            {
                'fields': (
                    'layout_settings',
                    'filters',
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

    inlines = [
        DashboardWidgetInline,
        DashboardShareInline,
    ]


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'dashboard',
        'widget_type',
        'analysis_result',
        'display_order',
        'is_visible',
        'created_at',
    )

    list_filter = (
        'widget_type',
        'is_visible',
        'created_at',
    )

    search_fields = (
        'title',
        'dashboard__name',
        'dashboard__owner__username',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    fieldsets = (
        (
            'بيانات العنصر',
            {
                'fields': (
                    'dashboard',
                    'analysis_result',
                    'title',
                    'widget_type',
                    'is_visible',
                )
            },
        ),
        (
            'إعدادات البيانات',
            {
                'fields': (
                    'x_column',
                    'y_column',
                    'aggregation',
                )
            },
        ),
        (
            'الموقع والحجم',
            {
                'fields': (
                    'position_x',
                    'position_y',
                    'width',
                    'height',
                    'display_order',
                )
            },
        ),
        (
            'إعدادات إضافية',
            {
                'fields': (
                    'settings',
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


@admin.register(DashboardShare)
class DashboardShareAdmin(admin.ModelAdmin):
    list_display = (
        'dashboard',
        'shared_with',
        'permission',
        'shared_at',
    )

    list_filter = (
        'permission',
        'shared_at',
    )

    search_fields = (
        'dashboard__name',
        'shared_with__username',
        'shared_with__email',
    )

    readonly_fields = (
        'shared_at',
    )