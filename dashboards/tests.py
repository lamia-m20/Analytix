from django.test import TestCase
from django.urls import reverse


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

    def test_login_and_dataset_pages_remain_available(self):
        login_response = self.client.get(reverse('accounts:login'))
        dataset_response = self.client.get(reverse('datasets:list'))

        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(dataset_response.status_code, 302)
