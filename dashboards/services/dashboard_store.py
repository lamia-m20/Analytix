from django.db import transaction

from dashboards.models import Dashboard
from dashboards.models import DashboardWidget
from datasets.models import Dataset


DEFAULT_WIDGETS = (
    {
        'title': 'عدد الصفوف والأعمدة في كل ورقة',
        'widget_type': 'bar',
        'source': 'sheet_dimensions',
    },
    {
        'title': 'القيم الفارغة في كل ورقة',
        'widget_type': 'pie',
        'source': 'missing_values',
    },
    {
        'title': 'متوسط الأعمدة الرقمية',
        'widget_type': 'bar',
        'source': 'numeric_means',
        'requires_numeric': True,
    },
    {
        'title': 'أعلى وأقل القيم الرقمية',
        'widget_type': 'line',
        'source': 'numeric_ranges',
        'requires_numeric': True,
    },
)


@transaction.atomic
def get_or_create_dataset_dashboard(
    dataset,
    *,
    has_numeric_columns,
):
    locked_dataset = (
        Dataset.objects
        .select_for_update()
        .get(
            pk=dataset.pk,
            user=dataset.user,
        )
    )

    dashboard = (
        Dashboard.objects
        .filter(
            owner=locked_dataset.user,
            layout_settings__dataset_id=locked_dataset.pk,
        )
        .first()
    )

    if dashboard is None:
        dashboard = Dashboard.objects.create(
            owner=locked_dataset.user,
            name=f'داشبورد {locked_dataset.title}',
            description=(
                f'لوحة معلومات ملف {locked_dataset.original_filename}'
            ),
            layout_settings={
                'dataset_id': locked_dataset.pk,
                'defaults_initialized': False,
            },
        )

    settings = dict(dashboard.layout_settings or {})

    if not settings.get('defaults_initialized'):
        widgets = []

        for order, definition in enumerate(DEFAULT_WIDGETS):
            if (
                definition.get('requires_numeric')
                and not has_numeric_columns
            ):
                continue

            widgets.append(
                DashboardWidget(
                    dashboard=dashboard,
                    title=definition['title'],
                    widget_type=definition['widget_type'],
                    display_order=order,
                    settings={
                        'source': definition['source'],
                    },
                )
            )

        DashboardWidget.objects.bulk_create(widgets)

        settings['dataset_id'] = locked_dataset.pk
        settings['defaults_initialized'] = True
        dashboard.layout_settings = settings
        dashboard.save(
            update_fields=[
                'layout_settings',
                'updated_at',
            ]
        )

    return (
        Dashboard.objects
        .prefetch_related('widgets')
        .get(
            pk=dashboard.pk,
            owner=locked_dataset.user,
        )
    )
