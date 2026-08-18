from django.test import TestCase
from django.urls import reverse
from django.template.loader import render_to_string
from types import SimpleNamespace
from django.contrib.auth import get_user_model

from analysis.models import AnalysisJob
from datasets.models import Dataset, DatasetSheet
from dashboards.models import Dashboard


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

    def test_home_has_single_analysis_cta_and_no_file_upload_controls(self):
        response = self.client.get(reverse('dashboards:home'))
        self.assertContains(
            response,
            f'<a class="button primary" href="{reverse("datasets:upload")}">ابدأ التحليل</a>',
            html=False,
        )
        self.assertNotContains(response, 'id="home-file-input"')
        self.assertNotContains(response, 'id="home-selected-file"')
        self.assertNotContains(response, 'type="file"')

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


class SidebarNavigationTests(TestCase):
    protected_pages = (
        'datasets:my_analyses',
        'analysis:list',
        'dashboards:list',
        'reports:list',
        'datasets:history',
        'accounts:settings',
    )

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='navigation-user',
            password='test-password',
        )
        self.other = get_user_model().objects.create_user(username='other-user')

    def _data_for(self, user, title):
        dataset = Dataset.objects.create(
            user=user,
            title=title,
            file=f'test/{title}.xlsx',
            status='ready',
        )
        sheet = DatasetSheet.objects.create(dataset=dataset, name='Sheet1')
        AnalysisJob.objects.create(
            owner=user,
            dataset=dataset,
            sheet=sheet,
            name=f'تحليل {title}',
            status='completed',
        )
        Dashboard.objects.create(
            owner=user,
            name=f'لوحة {title}',
            layout_settings={'dataset_id': dataset.pk},
        )
        return dataset

    def test_sidebar_links_have_distinct_functional_urls(self):
        response = self.client.get(reverse('dashboards:home'))
        urls = [reverse(name) for name in self.protected_pages]
        for url in urls:
            self.assertContains(response, f'href="{url}"')
        self.assertEqual(len(urls), len(set(urls)))
        self.assertNotEqual(reverse('datasets:my_analyses'), reverse('datasets:list'))

    def test_all_sidebar_pages_require_login(self):
        for name in self.protected_pages:
            with self.subTest(name=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 302)

    def test_pages_are_real_and_only_show_current_user_data(self):
        own = self._data_for(self.user, 'ملف المستخدم')
        self._data_for(self.other, 'ملف مستخدم آخر')
        self.client.force_login(self.user)

        expected = {
            'datasets:my_analyses': own.title,
            'analysis:list': f'تحليل {own.title}',
            'dashboards:list': f'لوحة {own.title}',
            'reports:list': own.title,
            'datasets:history': own.title,
            'accounts:settings': self.user.username,
        }
        for name, text in expected.items():
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, text)
                self.assertNotContains(response, 'ملف مستخدم آخر')
                self.assertContains(response, 'workspace-sidebar')

    def test_active_sidebar_link_matches_current_page(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('dashboards:list'))
        self.assertContains(
            response,
            f'<a class="active" href="{reverse("dashboards:list")}">',
            html=False,
        )
