from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


app_name = 'accounts'


urlpatterns = [
    path(
        'register/',
        views.register_view,
        name='register',
    ),

    path(
        'login/',
        views.login_view,
        name='login',
    ),

    path(
        'logout/',
        views.logout_view,
        name='logout',
    ),

    path(
        'password-reset/',
        views.password_reset_request_view,
        name='password_reset',
    ),

    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts-templates/password_reset_done.html',
        ),
        name='password_reset_done',
    ),

    path(
        'password-reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts-templates/password_reset_confirm.html',
            success_url='/accounts/password-reset/complete/',
        ),
        name='password_reset_confirm',
    ),

    path(
        'password-reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts-templates/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
]
