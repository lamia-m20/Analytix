from django.test import TestCase
from django.urls import reverse
from django.template.loader import render_to_string
from types import SimpleNamespace


class HomePageTests(TestCase):
    def test_home_workspace_contains_required_sections(self):
        response = self.client.get(reverse('dashboards:home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'workspace-sidebar')
        self.assertContains(response, 'كل ما تحتاجه لفهم بياناتك')
        self.assertContains(response, 'feature-dashboard')
        self.assertContains(response, 'الرسوم البيانية التفاعلية')
        self.assertContains(response, 'جودة البيانات')
        self.assertContains(response, 'مساعد Analytix')
        self.assertContains(response, reverse('accounts:login'))
        self.assertContains(response, reverse('datasets:list'))
        self.assertContains(response, 'id="feature-search"')
        self.assertContains(response, 'لا توجد نتائج مطابقة.')
        self.assertContains(response, 'id="assistant-question"')
        self.assertContains(response, 'id="assistant-send"')
        self.assertContains(response, 'id="assistant-answer"')
        self.assertContains(response, 'data-search-title="مساعد Analytix"')
        self.assertContains(response, 'اسأل عن إمكانات')
        self.assertContains(response, 'اسال عن امكانات')

    def test_login_and_dataset_pages_remain_available(self):
        login_response = self.client.get(reverse('accounts:login'))
        dataset_response = self.client.get(reverse('datasets:list'))

        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(dataset_response.status_code, 302)

    def test_analysis_search_index_contains_dashboard_and_dynamic_sheet(self):
        html = render_to_string(
            'datasets-templates/dataset_home.html',
            {
                'analysis_complete': True,
                'dataset': SimpleNamespace(pk=1, status='ready'),
                'file_name': 'weights.xlsx',
                'sheets_count': 1,
                'total_rows': 2,
                'total_columns': 2,
                'total_missing_values': 0,
                'total_numeric_columns': 1,
                'sheets_analysis': [{
                    'name': 'ورقة الأوزان',
                    'has_data': True,
                    'rows_count': 2,
                    'columns_count': 2,
                    'missing_count': 0,
                    'numeric_columns_count': 1,
                    'columns': ['الاسم', 'الوزن'],
                    'column_types': [],
                    'missing_values': [],
                    'numeric_statistics': [],
                    'preview_rows': [],
                }],
                'custom_widget_charts': [],
            },
        )

        self.assertIn('data-search-title="لوحة المعلومات"', html)
        self.assertIn('داشبورد', html)
        self.assertIn('data-search-title="ورقة ورقة الأوزان"', html)
        self.assertIn('أسماء الأعمدة أعمدة الاسم الوزن', html)
        self.assertIn('لا توجد نتائج مطابقة.', html)
