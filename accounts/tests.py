from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='correct-password',
        )

    def test_invalid_credentials_show_arabic_error_message(self):
        response = self.client.post(
            reverse('accounts:login'),
            {
                'username': self.user.username,
                'password': 'wrong-password',
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'اسم المستخدم أو كلمة المرور غير صحيحة.',
        )
        self.assertContains(response, 'role="alert"')

    def test_valid_credentials_log_user_in(self):
        response = self.client.post(
            reverse('accounts:login'),
            {
                'username': self.user.username,
                'password': 'correct-password',
            },
        )

        self.assertRedirects(response, '/')
        self.assertEqual(
            int(self.client.session['_auth_user_id']),
            self.user.pk,
        )


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
)
class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='resetuser',
            email='reset@example.com',
            password='old-password-123',
        )

    def test_password_reset_email_contains_change_link(self):
        response = self.client.post(
            reverse('accounts:password_reset'),
            {'username': self.user.username},
        )

        self.assertRedirects(
            response,
            reverse('accounts:password_reset_done'),
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(
            'إعادة تعيين كلمة المرور',
            mail.outbox[0].subject,
        )
        self.assertIn('/accounts/password-reset/', mail.outbox[0].body)

    def test_unknown_username_does_not_reveal_account_status(self):
        response = self.client.post(
            reverse('accounts:password_reset'),
            {'username': 'unknown-user'},
        )

        self.assertRedirects(
            response,
            reverse('accounts:password_reset_done'),
        )
        self.assertEqual(len(mail.outbox), 0)

    def test_username_is_required_before_requesting_reset(self):
        response = self.client.post(
            reverse('accounts:password_reset'),
            {'username': ''},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            'أدخل اسم المستخدم أولًا',
        )
        self.assertEqual(len(mail.outbox), 0)
