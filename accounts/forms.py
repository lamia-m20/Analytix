from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db import transaction

from .models import UserProfile


User = get_user_model()


class RegisterForm(UserCreationForm):
    first_name = forms.CharField(
        max_length=150,
        label='الاسم الأول',
        widget=forms.TextInput(
            attrs={
                'class': 'form-input',
                'placeholder': 'أدخل الاسم الأول',
                'autocomplete': 'given-name',
            }
        ),
    )

    last_name = forms.CharField(
        max_length=150,
        label='اسم العائلة',
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-input',
                'placeholder': 'أدخل اسم العائلة',
                'autocomplete': 'family-name',
            }
        ),
    )

    email = forms.EmailField(
        label='البريد الإلكتروني',
        widget=forms.EmailInput(
            attrs={
                'class': 'form-input',
                'placeholder': 'example@email.com',
                'autocomplete': 'email',
            }
        ),
    )

    account_type = forms.ChoiceField(
        choices=UserProfile.ACCOUNT_TYPES,
        label='نوع الحساب',
        widget=forms.Select(
            attrs={
                'class': 'form-input',
                'id': 'account-type',
            }
        ),
    )

    company_name = forms.CharField(
        max_length=200,
        label='اسم الشركة أو المؤسسة',
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-input',
                'placeholder': 'أدخل اسم الشركة أو المؤسسة',
                'id': 'company-name',
            }
        ),
    )

    phone = forms.CharField(
        max_length=30,
        label='رقم الهاتف',
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-input',
                'placeholder': '05xxxxxxxx',
                'autocomplete': 'tel',
            }
        ),
    )

    profile_image = forms.ImageField(
        label='الصورة الشخصية',
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                'class': 'file-input',
                'accept': 'image/*',
            }
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User

        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'account_type',
            'company_name',
            'phone',
            'profile_image',
            'password1',
            'password2',
        ]

        labels = {
            'username': 'اسم المستخدم',
            'password1': 'كلمة المرور',
            'password2': 'تأكيد كلمة المرور',
        }

        widgets = {
            'username': forms.TextInput(
                attrs={
                    'class': 'form-input',
                    'placeholder': 'أدخل اسم المستخدم',
                    'autocomplete': 'username',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['password1'].widget.attrs.update(
            {
                'class': 'form-input',
                'placeholder': 'أدخل كلمة المرور',
                'autocomplete': 'new-password',
            }
        )

        self.fields['password2'].widget.attrs.update(
            {
                'class': 'form-input',
                'placeholder': 'أعد كتابة كلمة المرور',
                'autocomplete': 'new-password',
            }
        )

        self.order_fields(
            [
                'first_name',
                'last_name',
                'username',
                'email',
                'account_type',
                'company_name',
                'phone',
                'profile_image',
                'password1',
                'password2',
            ]
        )

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'يوجد حساب مسجل بهذا البريد الإلكتروني.'
            )

        return email

    def clean(self):
        cleaned_data = super().clean()

        account_type = cleaned_data.get('account_type')
        company_name = cleaned_data.get('company_name', '').strip()

        if account_type in ['company', 'manager'] and not company_name:
            self.add_error(
                'company_name',
                'اسم الشركة أو المؤسسة مطلوب لهذا النوع من الحسابات.',
            )

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)

        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data.get('last_name', '')
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

            UserProfile.objects.create(
                user=user,
                account_type=self.cleaned_data['account_type'],
                company_name=self.cleaned_data.get('company_name', ''),
                phone=self.cleaned_data.get('phone', ''),
                profile_image=self.cleaned_data.get('profile_image'),
            )

        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='اسم المستخدم',
        widget=forms.TextInput(
            attrs={
                'class': 'form-input',
                'placeholder': 'أدخل اسم المستخدم',
                'autocomplete': 'username',
                'autofocus': True,
            }
        ),
    )

    password = forms.CharField(
        label='كلمة المرور',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-input',
                'placeholder': 'أدخل كلمة المرور',
                'autocomplete': 'current-password',
            }
        ),
    )