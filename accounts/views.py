from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.db import transaction
from django.shortcuts import redirect, render

from .forms import AccountSettingsForm, ProfileImageForm, ProfileSettingsForm
from .models import UserProfile


def register_view(request):
    if request.user.is_authenticated:
        return redirect('/')

    error_message = None

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get(
            'password_confirm',
            '',
        )

        if not first_name or not username or not email or not password:
            error_message = 'يرجى تعبئة جميع الحقول المطلوبة.'

        elif password != password_confirm:
            error_message = 'كلمتا المرور غير متطابقتين.'

        elif len(password) < 8:
            error_message = 'كلمة المرور يجب أن تكون 8 أحرف على الأقل.'

        elif User.objects.filter(username=username).exists():
            error_message = 'اسم المستخدم مستخدم مسبقًا.'

        elif User.objects.filter(email=email).exists():
            error_message = 'البريد الإلكتروني مستخدم مسبقًا.'

        else:
            User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )

            # بعد إنشاء الحساب ينتقل إلى تسجيل الدخول
            return redirect('accounts:login')

    return render(
        request,
        'accounts-templates/register.html',
        {
            'error_message': error_message,
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')

    error_message = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user is not None:
            login(request, user)
            return redirect('/')

        error_message = 'اسم المستخدم أو كلمة المرور غير صحيحة.'

    return render(
        request,
        'accounts-templates/login.html',
        {
            'error_message': error_message,
        },
    )


def password_reset_request_view(request):
    if request.method != 'POST':
        return redirect('accounts:login')

    username = request.POST.get('username', '').strip()

    if not username:
        return render(
            request,
            'accounts-templates/login.html',
            {
                'error_message': (
                    'أدخل اسم المستخدم أولًا ثم اضغط '
                    'على نسيت كلمة المرور.'
                ),
            },
        )

    user = User.objects.filter(
        username__iexact=username,
        is_active=True,
    ).first()

    # لا نكشف للزائر ما إذا كان اسم المستخدم أو البريد مسجلًا.
    if user and user.email:
        reset_form = PasswordResetForm(
            {'email': user.email},
        )

        if reset_form.is_valid():
            reset_form.save(
                request=request,
                use_https=request.is_secure(),
                email_template_name=(
                    'accounts-templates/password_reset_email.txt'
                ),
                subject_template_name=(
                    'accounts-templates/password_reset_subject.txt'
                ),
            )

    return redirect('accounts:password_reset_done')


def logout_view(request):
    logout(request)
    return redirect('/')


@login_required
def settings_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    section = request.GET.get('section', 'profile')
    if section not in {'profile', 'password', 'preferences', 'security'}:
        section = 'profile'

    account_form = AccountSettingsForm(instance=request.user)
    profile_form = ProfileSettingsForm(instance=profile)
    image_form = ProfileImageForm(instance=profile)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'profile':
            account_form = AccountSettingsForm(request.POST, instance=request.user)
            profile_form = ProfileSettingsForm(request.POST, instance=profile)
            if account_form.is_valid() and profile_form.is_valid():
                with transaction.atomic():
                    account_form.save()
                    profile_form.save()
                messages.success(request, 'تم حفظ تغييرات الملف الشخصي بنجاح.')
                return redirect('accounts:settings')
            section = 'profile'
        elif action == 'upload_image':
            image_form = ProfileImageForm(request.POST, request.FILES, instance=profile)
            if image_form.is_valid():
                old_image = profile.profile_image
                image_form.save()
                if old_image and old_image.name != profile.profile_image.name:
                    old_image.delete(save=False)
                messages.success(request, 'تم تحديث صورة الحساب بنجاح.')
                return redirect('accounts:settings')
            section = 'profile'
        elif action == 'delete_image' and profile.profile_image:
            profile.profile_image.delete(save=False)
            profile.profile_image = None
            profile.save(update_fields=['profile_image', 'updated_at'])
            messages.success(request, 'تم حذف صورة الحساب.')
            return redirect('accounts:settings')
        elif action == 'send_password_reset':
            section = 'password'
            if request.user.email:
                reset_form = PasswordResetForm({'email': request.user.email})
                if reset_form.is_valid():
                    reset_form.save(
                        request=request,
                        use_https=request.is_secure(),
                        email_template_name='accounts-templates/password_reset_email.txt',
                        subject_template_name='accounts-templates/password_reset_subject.txt',
                    )
                messages.success(
                    request,
                    'تم إرسال رابط تغيير كلمة المرور إلى بريدك الإلكتروني.',
                )
            else:
                messages.error(
                    request,
                    'لا يوجد بريد إلكتروني مرتبط بالحساب لإرسال الرابط.',
                )
            return redirect('/accounts/settings/?section=password')

    return render(
        request,
        'accounts-templates/settings.html',
        {
            'profile': profile,
            'section': section,
            'account_form': account_form,
            'profile_form': profile_form,
            'image_form': image_form,
        },
    )
