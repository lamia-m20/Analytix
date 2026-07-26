from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render


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


def logout_view(request):
    logout(request)
    return redirect('/')