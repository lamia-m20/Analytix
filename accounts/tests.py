from django.contrib.auth.models import User
from io import BytesIO
import shutil
import tempfile

from PIL import Image
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test import override_settings
from django.urls import reverse

from .models import UserProfile


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
        self.assertContains(response, 'أدخل اسم المستخدم أولًا')
        self.assertEqual(len(mail.outbox), 0)


class AccountSettingsTests(TestCase):
    def setUp(self):
        self.media_dir = tempfile.mkdtemp()
        self.storage_override = override_settings(
            MEDIA_ROOT=self.media_dir,
            STORAGES={
                'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
                'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
            },
        )
        self.storage_override.enable()
        self.addCleanup(self.storage_override.disable)
        self.addCleanup(shutil.rmtree, self.media_dir, True)
        self.user = User.objects.create_user(
            username='settings-user',
            email='old@example.com',
            password='old-password-123',
        )
        self.profile = UserProfile.objects.create(user=self.user)
        self.client.force_login(self.user)

    def _image(self, name='avatar.png', image_format='PNG'):
        buffer = BytesIO()
        Image.new('RGB', (40, 40), '#356ee8').save(buffer, format=image_format)
        return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')

    def test_settings_sections_render(self):
        for section, heading in (
            ('profile', 'الملف الشخصي'),
            ('password', 'كلمة المرور'),
            ('preferences', 'التفضيلات'),
            ('security', 'الأمان'),
        ):
            with self.subTest(section=section):
                response = self.client.get(reverse('accounts:settings'), {'section': section})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, heading)

    def test_profile_fields_are_saved(self):
        response = self.client.post(reverse('accounts:settings'), {
            'action': 'profile', 'username': 'updated-user',
            'email': 'new@example.com', 'first_name': 'محمد', 'last_name': 'أحمد',
            'phone': '0500000000', 'company_name': 'Analytix',
            'account_type': 'analyst',
        })
        self.assertRedirects(response, reverse('accounts:settings'))
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.user.username, 'updated-user')
        self.assertEqual(self.profile.phone, '0500000000')

    def test_image_can_be_uploaded_replaced_and_deleted(self):
        response = self.client.post(
            reverse('accounts:settings'),
            {'action': 'upload_image', 'profile_image': self._image()},
        )
        self.assertRedirects(response, reverse('accounts:settings'))
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.profile_image.name.endswith('.png'))
        first_name = self.profile.profile_image.name
        home = self.client.get(reverse('dashboards:home'))
        self.assertContains(home, self.profile.profile_image.url)

        response = self.client.post(
            reverse('accounts:settings'),
            {'action': 'upload_image', 'profile_image': self._image('new-avatar.png')},
        )
        self.assertRedirects(response, reverse('accounts:settings'))
        self.profile.refresh_from_db()
        self.assertNotEqual(self.profile.profile_image.name, first_name)

        response = self.client.post(
            reverse('accounts:settings'), {'action': 'delete_image'}
        )
        self.assertRedirects(response, reverse('accounts:settings'))
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.profile_image)

    def test_invalid_image_is_rejected(self):
        invalid = SimpleUploadedFile('avatar.txt', b'not-an-image', content_type='text/plain')
        response = self.client.post(
            reverse('accounts:settings'),
            {'action': 'upload_image', 'profile_image': invalid},
        )
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.profile_image)
        self.assertContains(response, 'قم برفع صورة صحيحة')

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_password_section_sends_existing_reset_email(self):
        mail.outbox.clear()
        response = self.client.post(
            reverse('accounts:settings') + '?section=password',
            {'action': 'send_password_reset'},
        )
        self.assertRedirects(
            response,
            reverse('accounts:settings') + '?section=password',
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn('/accounts/password-reset/', mail.outbox[0].body)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('old-password-123'))

    def test_password_section_has_no_direct_password_fields(self):
        response = self.client.get(
            reverse('accounts:settings'), {'section': 'password'}
        )
        self.assertNotContains(response, 'old_password')
        self.assertNotContains(response, 'new_password1')
        self.assertNotContains(response, 'Old password')
        self.assertContains(response, 'إرسال رابط تغيير كلمة المرور')

    def test_preferences_hide_unreliable_monthly_usage(self):
        response = self.client.get(
            reverse('accounts:settings'), {'section': 'preferences'}
        )
        self.assertContains(response, 'الحد الأقصى لحجم ملف Excel')
        self.assertNotContains(response, 'الحد الشهري للتحليلات')
        self.assertNotContains(response, 'التحليلات المتبقية')

    def test_security_hides_profile_verification(self):
        response = self.client.get(
            reverse('accounts:settings'), {'section': 'security'}
        )
        self.assertNotContains(response, 'توثيق الملف الشخصي')
        self.assertNotContains(response, 'غير موثق')
        self.assertContains(response, 'آخر تسجيل دخول')
