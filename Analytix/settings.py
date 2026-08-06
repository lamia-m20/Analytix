import os
from pathlib import Path

from dotenv import load_dotenv


# ==========================================
# المسار الرئيسي للمشروع
# ==========================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ==========================================
# تحميل متغيرات ملف .env
# ==========================================

load_dotenv(BASE_DIR / '.env')


# ==========================================
# دوال مساعدة لقراءة متغيرات البيئة
# ==========================================

def get_boolean_env(name, default=False):
    """
    تحويل قيمة متغير البيئة إلى Boolean.

    القيم التي تعتبر True:
    true, 1, yes, on
    """

    value = os.getenv(
        name,
        str(default),
    )

    return value.strip().lower() in {
        'true',
        '1',
        'yes',
        'on',
    }


def get_list_env(name, default=''):
    """
    تحويل قيمة مفصولة بفواصل إلى قائمة.

    مثال:

    ALLOWED_HOSTS=localhost,127.0.0.1,example.com
    """

    value = os.getenv(
        name,
        default,
    )

    return [
        item.strip()
        for item in value.split(',')
        if item.strip()
    ]


# ==========================================
# إعدادات الأمان
# ==========================================

SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-change-this-secret-key',
)

DEBUG = get_boolean_env(
    'DEBUG',
    True,
)

ALLOWED_HOSTS = get_list_env(
    'ALLOWED_HOSTS',
    (
        '127.0.0.1,'
        'localhost,'
        'analytix-cc2w.onrender.com'
    ),
)


# ==========================================
# النطاقات الموثوقة لطلبات CSRF
# ==========================================

CSRF_TRUSTED_ORIGINS = get_list_env(
    'CSRF_TRUSTED_ORIGINS',
    'https://analytix-cc2w.onrender.com',
)


# ==========================================
# إعدادات Render
# ==========================================

RENDER_EXTERNAL_HOSTNAME = os.getenv(
    'RENDER_EXTERNAL_HOSTNAME',
    '',
).strip()


if RENDER_EXTERNAL_HOSTNAME:
    if RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(
            RENDER_EXTERNAL_HOSTNAME
        )

    render_origin = (
        f'https://{RENDER_EXTERNAL_HOSTNAME}'
    )

    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(
            render_origin
        )


# ==========================================
# التطبيقات المثبتة
# ==========================================

INSTALLED_APPS = [
    # تطبيقات Django الأساسية
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # تطبيقات Cloudinary
    'cloudinary_storage',
    'cloudinary',

    # تطبيقات المشروع
    'accounts.apps.AccountsConfig',
    'datasets.apps.DatasetsConfig',
    'analysis.apps.AnalysisConfig',
    'dashboards.apps.DashboardsConfig',
    'reports.apps.ReportsConfig',
]


# ==========================================
# الوسائط البرمجية Middleware
# ==========================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',

    # دعم اللغة والترجمة
    'django.middleware.locale.LocaleMiddleware',

    'django.middleware.common.CommonMiddleware',

    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',

    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ==========================================
# ملف الروابط الرئيسي
# ==========================================

ROOT_URLCONF = 'Analytix.urls'


# ==========================================
# إعدادات القوالب Templates
# ==========================================

TEMPLATES = [
    {
        'BACKEND': (
            'django.template.backends.django.'
            'DjangoTemplates'
        ),

        'DIRS': [
            BASE_DIR / 'templates',
        ],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                (
                    'django.template.context_processors.'
                    'request'
                ),
                (
                    'django.contrib.auth.context_processors.'
                    'auth'
                ),
                (
                    'django.contrib.messages.context_processors.'
                    'messages'
                ),
            ],
        },
    },
]


# ==========================================
# إعدادات WSGI
# ==========================================

WSGI_APPLICATION = 'Analytix.wsgi.application'


# ==========================================
# إعداد قاعدة البيانات
# ==========================================

# القيم المدعومة:
#
# sqlite:
# تستخدم في التطوير المحلي.
#
# postgres:
# تستخدم في الإنتاج على Render.

DATABASE_ENGINE = os.getenv(
    'DATABASE_ENGINE',
    'sqlite',
).strip().lower()


if DATABASE_ENGINE == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': (
                'django.db.backends.postgresql'
            ),

            'NAME': os.getenv(
                'POSTGRES_DB',
                'db_analytix',
            ),

            'USER': os.getenv(
                'POSTGRES_USER',
                'db_analytix_user',
            ),

            'PASSWORD': os.getenv(
                'POSTGRES_PASSWORD',
                '',
            ),

            'HOST': os.getenv(
                'POSTGRES_HOST',
                '',
            ),

            'PORT': os.getenv(
                'POSTGRES_PORT',
                '5432',
            ),

            'CONN_MAX_AGE': int(
                os.getenv(
                    'DATABASE_CONN_MAX_AGE',
                    '60',
                )
            ),

            'OPTIONS': {
                'connect_timeout': int(
                    os.getenv(
                        'DATABASE_CONNECT_TIMEOUT',
                        '10',
                    )
                ),
            },
        },
    }

else:
    DATABASES = {
        'default': {
            'ENGINE': (
                'django.db.backends.sqlite3'
            ),

            'NAME': (
                BASE_DIR
                / os.getenv(
                    'SQLITE_NAME',
                    'db.sqlite3',
                )
            ),
        },
    }


# ==========================================
# التحقق من كلمات المرور
# ==========================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'UserAttributeSimilarityValidator'
        ),
    },

    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'MinimumLengthValidator'
        ),
    },

    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'CommonPasswordValidator'
        ),
    },

    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'NumericPasswordValidator'
        ),
    },
]


# ==========================================
# إعدادات اللغة والتوقيت
# ==========================================

LANGUAGE_CODE = 'ar'

TIME_ZONE = 'Asia/Riyadh'

USE_I18N = True

USE_TZ = True


# ==========================================
# إعدادات Cloudinary
# ==========================================

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.getenv(
        'CLOUDINARY_CLOUD_NAME',
        '',
    ),

    'API_KEY': os.getenv(
        'CLOUDINARY_API_KEY',
        '',
    ),

    'API_SECRET': os.getenv(
        'CLOUDINARY_API_SECRET',
        '',
    ),

    # إنشاء روابط HTTPS
    'SECURE': True,
}


# ==========================================
# أنظمة تخزين الملفات
# ==========================================

STORAGES = {
    # تخزين ملفات Excel وملفات النتائج
    # في Cloudinary بصيغة Raw.
    'default': {
        'BACKEND': (
            'cloudinary_storage.storage.'
            'RawMediaCloudinaryStorage'
        ),
    },

    # تخزين ملفات static الخاصة بالتصميم.
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}


# ==========================================
# إعدادات الملفات الثابتة Static Files
# ==========================================

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'


# ==========================================
# إعدادات ملفات الوسائط Media Files
# ==========================================

MEDIA_URL = '/media/'

# يستخدم هذا المسار أثناء التطوير المحلي
# وبعض العمليات المؤقتة.
#
# التخزين الافتراضي للملفات المرفوعة هو Cloudinary.
MEDIA_ROOT = BASE_DIR / 'media'


# ==========================================
# حدود رفع الملفات
# ==========================================

# الملفات الأكبر من 2 ميجابايت لا تبقى كاملة
# داخل ذاكرة السيرفر، بل تحفظ مؤقتًا على القرص.
FILE_UPLOAD_MAX_MEMORY_SIZE = (
    2 * 1024 * 1024
)

# الحد الأعلى لحجم بيانات طلب HTTP كاملًا.
#
# الحد هنا 12 ميجابايت لإتاحة رفع ملف حجمه
# 10 ميجابايت مع بيانات النموذج الإضافية.
DATA_UPLOAD_MAX_MEMORY_SIZE = (
    12 * 1024 * 1024
)


# ==========================================
# إعدادات تسجيل الدخول والخروج
# ==========================================

LOGIN_URL = 'accounts:login'

LOGIN_REDIRECT_URL = '/'

LOGOUT_REDIRECT_URL = 'accounts:login'


# ==========================================
# إعدادات البريد الإلكتروني واستعادة المرور
# ==========================================

EMAIL_BACKEND = os.getenv(
    'EMAIL_BACKEND',
    (
        'django.core.mail.backends.console.EmailBackend'
        if DEBUG
        else 'django.core.mail.backends.smtp.EmailBackend'
    ),
)

EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = ''.join(
    os.getenv('EMAIL_HOST_PASSWORD', '').split()
)
EMAIL_USE_TLS = get_boolean_env('EMAIL_USE_TLS', True)
DEFAULT_FROM_EMAIL = os.getenv(
    'DEFAULT_FROM_EMAIL',
    EMAIL_HOST_USER or 'Analytix <no-reply@analytix.local>',
)

# رابط استعادة كلمة المرور صالح لمدة ساعة.
PASSWORD_RESET_TIMEOUT = 60 * 60


# ==========================================
# إعدادات الأمان الخاصة بالإنتاج
# ==========================================

SECURE_SSL_REDIRECT = get_boolean_env(
    'SECURE_SSL_REDIRECT',
    False,
)

SESSION_COOKIE_SECURE = get_boolean_env(
    'SESSION_COOKIE_SECURE',
    not DEBUG,
)

CSRF_COOKIE_SECURE = get_boolean_env(
    'CSRF_COOKIE_SECURE',
    not DEBUG,
)

SECURE_HSTS_SECONDS = int(
    os.getenv(
        'SECURE_HSTS_SECONDS',
        '0',
    )
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = (
    get_boolean_env(
        'SECURE_HSTS_INCLUDE_SUBDOMAINS',
        False,
    )
)

SECURE_HSTS_PRELOAD = get_boolean_env(
    'SECURE_HSTS_PRELOAD',
    False,
)


# Render يرسل نوع البروتوكول الحقيقي
# من خلال هذا الرأس.
SECURE_PROXY_SSL_HEADER = (
    'HTTP_X_FORWARDED_PROTO',
    'https',
)


# ==========================================
# إعدادات الجلسات والحماية
# ==========================================

SESSION_COOKIE_HTTPONLY = True

CSRF_COOKIE_HTTPONLY = False

X_FRAME_OPTIONS = 'DENY'


# ==========================================
# نوع المفتاح الافتراضي للنماذج
# ==========================================

DEFAULT_AUTO_FIELD = (
    'django.db.models.BigAutoField'
)
