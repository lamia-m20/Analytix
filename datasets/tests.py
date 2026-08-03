from io import BytesIO
import os
from unittest.mock import patch

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from dashboards.models import Dashboard
from dashboards.models import DashboardWidget
from dashboards.services.dashboard_ai import (
    DashboardAIUnavailableError,
)
from dashboards.services.dashboard_ai import (
    DashboardPlanValidationError,
)
from dashboards.services.dashboard_ai import (
    apply_dashboard_plan,
)
from dashboards.services.dashboard_ai import (
    request_dashboard_plan,
)
from dashboards.services.dashboard_store import (
    get_or_create_dataset_dashboard,
)

from .models import Dataset
from .models import DatasetColumn
from .models import DatasetSheet


class DatasetDashboardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='analyst',
            password='strong-test-password',
        )
        self.client.force_login(self.user)

    def _excel_file(self):
        buffer = BytesIO()

        with pd.ExcelWriter(
            buffer,
            engine='openpyxl',
        ) as writer:
            pd.DataFrame(
                {
                    'المبيعات': [100, 200, None],
                    'المنطقة': ['الرياض', 'جدة', 'الرياض'],
                }
            ).to_excel(
                writer,
                sheet_name='المبيعات',
                index=False,
            )
            pd.DataFrame(
                {
                    'الموظفون': [8, 12],
                }
            ).to_excel(
                writer,
                sheet_name='الفروع',
                index=False,
            )

        return SimpleUploadedFile(
            'بيانات.xlsx',
            buffer.getvalue(),
            content_type=(
                'application/vnd.openxmlformats-officedocument.'
                'spreadsheetml.sheet'
            ),
        )

    def _dataset_with_structure(self, user=None):
        dataset = Dataset.objects.create(
            user=user or self.user,
            title='ملف المبيعات',
            file='test/sales.xlsx',
            status='uploaded',
        )
        sheet = DatasetSheet.objects.create(
            dataset=dataset,
            name='المبيعات',
            row_count=3,
            column_count=2,
        )
        DatasetColumn.objects.bulk_create([
            DatasetColumn(
                sheet=sheet,
                name='الشهر',
                position=0,
                data_type='object',
            ),
            DatasetColumn(
                sheet=sheet,
                name='القيمة',
                position=1,
                data_type='float64',
            ),
        ])
        return dataset

    def test_dashboard_page_loads(self):
        response = self.client.get(
            reverse('datasets:list')
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ابدأ التحليل')

    def test_excel_upload_creates_analysis_context(self):
        response = self.client.post(
            reverse('datasets:list'),
            {'excel_file': self._excel_file()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['analysis_complete'])
        self.assertEqual(response.context['sheets_count'], 2)
        self.assertEqual(response.context['total_rows'], 5)
        self.assertEqual(response.context['total_columns'], 3)
        self.assertEqual(
            response.context['total_missing_values'],
            1,
        )
        self.assertContains(response, 'لوحة المعلومات')

    def test_non_excel_file_is_rejected(self):
        response = self.client.post(
            reverse('datasets:list'),
            {
                'excel_file': SimpleUploadedFile(
                    'data.txt',
                    b'not an excel file',
                ),
            },
        )

        self.assertContains(
            response,
            'صيغة الملف غير مدعومة',
        )

    def test_dashboard_edit_request_displays_confirmation(self):
        dataset = self._dataset_with_structure()
        with patch(
            'datasets.views.request_dashboard_plan',
            return_value={
                'actions': [{
                    'action': 'add',
                    'title': 'المبيعات حسب الشهر',
                    'widget_type': 'chart',
                    'chart_type': 'bar',
                    'sheet_name': 'المبيعات',
                    'x_column': 'الشهر',
                    'y_column': 'القيمة',
                    'aggregation': 'sum',
                }],
            },
        ):
            response = self.client.post(
                reverse(
                    'datasets:edit_dashboard',
                    args=[dataset.pk],
                ),
                {
                    'dashboard_request': (
                        'أضف مخططًا للمبيعات حسب الشهر'
                    ),
                },
                follow=True,
            )

        self.assertRedirects(
            response,
            reverse(
                'datasets:detail',
                args=[dataset.pk],
            ),
        )
        self.assertContains(
            response,
            'تم تعديل 1 مخططات بنجاح.',
        )

    def test_dashboard_edit_endpoint_rejects_get(self):
        dataset = Dataset.objects.create(
            user=self.user,
            title='ملف المبيعات',
            file='test/sales.xlsx',
            status='uploaded',
        )
        response = self.client.get(
            reverse(
                'datasets:edit_dashboard',
                args=[dataset.pk],
            )
        )

        self.assertEqual(response.status_code, 405)

    def test_user_cannot_edit_another_users_dataset(self):
        other_user = get_user_model().objects.create_user(
            username='other-analyst',
            password='strong-test-password',
        )
        dataset = Dataset.objects.create(
            user=other_user,
            title='ملف خاص',
            file='test/private.xlsx',
            status='uploaded',
        )

        response = self.client.post(
            reverse(
                'datasets:edit_dashboard',
                args=[dataset.pk],
            ),
            {'dashboard_request': 'احذف المخطط'},
        )

        self.assertEqual(response.status_code, 404)

    def test_empty_dashboard_edit_request_is_rejected(self):
        dataset = Dataset.objects.create(
            user=self.user,
            title='ملف المبيعات',
            file='test/sales.xlsx',
            status='uploaded',
        )

        response = self.client.post(
            reverse(
                'datasets:edit_dashboard',
                args=[dataset.pk],
            ),
            {'dashboard_request': '   '},
            follow=True,
        )

        self.assertRedirects(
            response,
            reverse(
                'datasets:detail',
                args=[dataset.pk],
            ),
        )
        self.assertContains(
            response,
            'يرجى كتابة طلب تعديل الداشبورد.',
        )

    def test_dashboard_and_default_widgets_are_created_once(self):
        dataset = Dataset.objects.create(
            user=self.user,
            title='ملف المبيعات',
            file='test/sales.xlsx',
            status='ready',
        )

        first_dashboard = get_or_create_dataset_dashboard(
            dataset,
            has_numeric_columns=True,
        )
        first_widget_ids = list(
            first_dashboard.widgets.values_list(
                'pk',
                flat=True,
            )
        )

        second_dashboard = get_or_create_dataset_dashboard(
            dataset,
            has_numeric_columns=True,
        )
        second_widget_ids = list(
            second_dashboard.widgets.values_list(
                'pk',
                flat=True,
            )
        )

        self.assertEqual(first_dashboard.pk, second_dashboard.pk)
        self.assertEqual(first_widget_ids, second_widget_ids)
        self.assertEqual(
            Dashboard.objects.filter(
                owner=self.user,
                layout_settings__dataset_id=dataset.pk,
            ).count(),
            1,
        )
        self.assertEqual(len(first_widget_ids), 4)

    def test_saved_widget_changes_survive_dashboard_reload(self):
        dataset = Dataset.objects.create(
            user=self.user,
            title='ملف المبيعات',
            file='test/sales.xlsx',
            status='ready',
        )
        dashboard = get_or_create_dataset_dashboard(
            dataset,
            has_numeric_columns=True,
        )
        widget = dashboard.widgets.get(
            settings__source='missing_values'
        )
        widget.widget_type = 'bar'
        widget.save(update_fields=['widget_type'])

        reloaded_dashboard = get_or_create_dataset_dashboard(
            dataset,
            has_numeric_columns=True,
        )
        reloaded_widget = DashboardWidget.objects.get(
            dashboard=reloaded_dashboard,
            settings__source='missing_values',
        )

        self.assertEqual(reloaded_widget.widget_type, 'bar')
        self.assertEqual(reloaded_dashboard.widgets.count(), 4)

    def test_user_cannot_open_another_users_dataset_dashboard(self):
        other_user = get_user_model().objects.create_user(
            username='dashboard-owner',
            password='strong-test-password',
        )
        dataset = Dataset.objects.create(
            user=other_user,
            title='ملف خاص',
            file='test/private.xlsx',
            status='ready',
        )

        response = self.client.get(
            reverse(
                'datasets:detail',
                args=[dataset.pk],
            )
        )

        self.assertEqual(response.status_code, 404)

    def test_anonymous_user_cannot_edit_dashboard(self):
        dataset = self._dataset_with_structure()
        self.client.logout()

        response = self.client.post(
            reverse(
                'datasets:edit_dashboard',
                args=[dataset.pk],
            ),
            {'dashboard_request': 'احذف المخطط'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_openai_failure_keeps_existing_widgets(self):
        dataset = self._dataset_with_structure()
        dashboard = get_or_create_dataset_dashboard(
            dataset,
            has_numeric_columns=True,
        )
        widget_ids = list(
            dashboard.widgets.values_list(
                'pk',
                flat=True,
            )
        )

        with patch(
            'datasets.views.request_dashboard_plan',
            side_effect=DashboardAIUnavailableError(
                'تعذر الاتصال بخدمة تعديل الداشبورد حاليًا.'
            ),
        ):
            response = self.client.post(
                reverse(
                    'datasets:edit_dashboard',
                    args=[dataset.pk],
                ),
                {'dashboard_request': 'غيّر المخطط'},
                follow=True,
            )

        self.assertContains(
            response,
            'تعذر الاتصال بخدمة تعديل الداشبورد حاليًا.',
        )
        self.assertEqual(
            list(
                dashboard.widgets.values_list(
                    'pk',
                    flat=True,
                )
            ),
            widget_ids,
        )


class DashboardAIServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='ai-analyst',
            password='strong-test-password',
        )
        self.dataset = Dataset.objects.create(
            user=self.user,
            title='المبيعات',
            file='test/sales.xlsx',
            status='ready',
        )
        self.dashboard = get_or_create_dataset_dashboard(
            self.dataset,
            has_numeric_columns=True,
        )
        self.metadata = {
            'sheets': [{
                'name': 'المبيعات',
                'columns': [
                    {'name': 'الشهر', 'type': 'object'},
                    {'name': 'القيمة', 'type': 'float64'},
                ],
            }],
            'widgets': [],
        }

    def _apply(self, actions):
        return apply_dashboard_plan(
            dashboard=self.dashboard,
            user=self.user,
            metadata=self.metadata,
            plan={
                'actions': actions,
                'message': '',
            },
        )

    def test_update_pie_to_bar(self):
        widget = self.dashboard.widgets.get(
            settings__source='missing_values'
        )

        count = self._apply([{
            'action': 'update',
            'widget_id': widget.pk,
            'chart_type': 'bar',
        }])

        widget.refresh_from_db()
        self.assertEqual(count, 1)
        self.assertEqual(widget.widget_type, 'bar')

    def test_delete_widget(self):
        widget = self.dashboard.widgets.first()

        count = self._apply([{
            'action': 'delete',
            'widget_id': widget.pk,
        }])

        self.assertEqual(count, 1)
        self.assertFalse(
            DashboardWidget.objects.filter(
                pk=widget.pk
            ).exists()
        )

    def test_add_widget_with_valid_columns(self):
        count = self._apply([{
            'action': 'add',
            'title': 'المبيعات الشهرية',
            'widget_type': 'chart',
            'chart_type': 'line',
            'sheet_name': 'المبيعات',
            'x_column': 'الشهر',
            'y_column': 'القيمة',
            'aggregation': 'sum',
        }])

        widget = self.dashboard.widgets.get(
            title='المبيعات الشهرية'
        )
        self.assertEqual(count, 1)
        self.assertEqual(widget.widget_type, 'line')
        self.assertEqual(
            widget.settings['sheet_name'],
            'المبيعات',
        )

    def test_rejects_unknown_column(self):
        with self.assertRaises(
            DashboardPlanValidationError
        ):
            self._apply([{
                'action': 'add',
                'title': 'مخطط خاطئ',
                'widget_type': 'chart',
                'chart_type': 'bar',
                'sheet_name': 'المبيعات',
                'x_column': 'عمود غير موجود',
                'y_column': 'القيمة',
                'aggregation': 'sum',
            }])

    def test_rejects_widget_from_another_dashboard(self):
        other_user = get_user_model().objects.create_user(
            username='other-ai-user',
            password='strong-test-password',
        )
        other_dashboard = Dashboard.objects.create(
            owner=other_user,
            name='لوحة أخرى',
        )
        foreign_widget = DashboardWidget.objects.create(
            dashboard=other_dashboard,
            title='عنصر خاص',
            widget_type='pie',
        )

        with self.assertRaises(
            DashboardPlanValidationError
        ):
            self._apply([{
                'action': 'delete',
                'widget_id': foreign_widget.pk,
            }])

        self.assertTrue(
            DashboardWidget.objects.filter(
                pk=foreign_widget.pk
            ).exists()
        )

    def test_rejects_invalid_chart_type(self):
        widget = self.dashboard.widgets.first()

        with self.assertRaises(
            DashboardPlanValidationError
        ):
            self._apply([{
                'action': 'update',
                'widget_id': widget.pk,
                'chart_type': 'scatter',
            }])

    def test_invalid_plan_json_shape_is_rejected(self):
        with self.assertRaises(
            DashboardPlanValidationError
        ):
            apply_dashboard_plan(
                dashboard=self.dashboard,
                user=self.user,
                metadata=self.metadata,
                plan={'actions': 'not-a-list'},
            )

    def test_transaction_rolls_back_all_actions(self):
        widget = self.dashboard.widgets.first()
        original_title = widget.title

        with self.assertRaises(
            DashboardPlanValidationError
        ):
            self._apply([
                {
                    'action': 'update',
                    'widget_id': widget.pk,
                    'title': 'عنوان مؤقت',
                },
                {
                    'action': 'add',
                    'title': 'مخطط خاطئ',
                    'widget_type': 'chart',
                    'chart_type': 'bar',
                    'sheet_name': 'المبيعات',
                    'x_column': 'غير موجود',
                    'y_column': 'القيمة',
                    'aggregation': 'sum',
                },
            ])

        widget.refresh_from_db()
        self.assertEqual(widget.title, original_title)

    def test_missing_api_key_returns_safe_arabic_error(self):
        with patch.dict(
            os.environ,
            {'OPENAI_API_KEY': ''},
        ):
            with self.assertRaisesRegex(
                DashboardAIUnavailableError,
                'غير مهيأة',
            ):
                request_dashboard_plan(
                    user_request='غيّر المخطط',
                    metadata=self.metadata,
                )

    def test_update_single_widget_colors(self):
        widget = self.dashboard.widgets.first()

        count = self._apply([{
            'action': 'update',
            'widget_id': widget.pk,
            'colors': ['#ec4899', '#facc15'],
        }])

        widget.refresh_from_db()
        self.assertEqual(count, 1)
        self.assertEqual(
            widget.settings['colors'],
            ['#ec4899', '#facc15'],
        )

    def test_update_all_dashboard_widget_colors(self):
        widgets = list(self.dashboard.widgets.all())
        actions = [
            {
                'action': 'update',
                'widget_id': widget.pk,
                'colors': ['#ec4899', '#facc15'],
            }
            for widget in widgets
        ]

        count = self._apply(actions)

        self.assertEqual(count, len(widgets))
        for widget in DashboardWidget.objects.filter(
            dashboard=self.dashboard
        ):
            self.assertEqual(
                widget.settings['colors'],
                ['#ec4899', '#facc15'],
            )

    def test_rejects_invalid_hex_color(self):
        widget = self.dashboard.widgets.first()

        with self.assertRaises(
            DashboardPlanValidationError
        ):
            self._apply([{
                'action': 'update',
                'widget_id': widget.pk,
                'colors': ['pink', 'javascript:alert(1)'],
            }])

        widget.refresh_from_db()
        self.assertNotIn(
            'colors',
            widget.settings,
        )

    def test_rejects_more_than_ten_colors(self):
        widget = self.dashboard.widgets.first()

        with self.assertRaises(
            DashboardPlanValidationError
        ):
            self._apply([{
                'action': 'update',
                'widget_id': widget.pk,
                'colors': ['#ec4899'] * 11,
            }])

    def test_widget_colors_survive_reload(self):
        widget = self.dashboard.widgets.first()
        self._apply([{
            'action': 'update',
            'widget_id': widget.pk,
            'colors': ['#3b82f6', '#22c55e'],
        }])

        reloaded_dashboard = get_or_create_dataset_dashboard(
            self.dataset,
            has_numeric_columns=True,
        )
        reloaded_widget = reloaded_dashboard.widgets.get(
            pk=widget.pk
        )

        self.assertEqual(
            reloaded_widget.settings['colors'],
            ['#3b82f6', '#22c55e'],
        )

    def test_cannot_change_colors_of_another_users_widget(self):
        other_user = get_user_model().objects.create_user(
            username='color-owner',
            password='strong-test-password',
        )
        other_dashboard = Dashboard.objects.create(
            owner=other_user,
            name='لوحة ألوان خاصة',
        )
        foreign_widget = DashboardWidget.objects.create(
            dashboard=other_dashboard,
            title='مخطط خاص',
            widget_type='pie',
        )

        with self.assertRaises(
            DashboardPlanValidationError
        ):
            self._apply([{
                'action': 'update',
                'widget_id': foreign_widget.pk,
                'colors': ['#ec4899'],
            }])

        foreign_widget.refresh_from_db()
        self.assertNotIn(
            'colors',
            foreign_widget.settings,
        )
