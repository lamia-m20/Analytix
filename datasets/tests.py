from io import BytesIO

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from dashboards.models import Dashboard
from dashboards.models import DashboardWidget
from dashboards.services.dashboard_store import (
    get_or_create_dataset_dashboard,
)

from .models import Dataset


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
            (
                'تم استلام طلبك: '
                'أضف مخططًا للمبيعات حسب الشهر'
            ),
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
