from io import BytesIO

import pandas as pd
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse


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
