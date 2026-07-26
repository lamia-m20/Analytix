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
    '127.0.0.1,localhost,analytix-cc2w.onrender.com',
)


# النطاقات الموثوقة لطلبات CSRF
CSRF_TRUSTED_ORIGINS = get_list_env(
    'CSRF_TRUSTED_ORIGINS',
    'https://analytix-cc2w.onrender.com',
)


# Render provides the deployed hostname through this environment variable.
RENDER_EXTERNAL_HOSTNAME = os.getenv(
    'RENDER_EXTERNAL_HOSTNAME',
    '',
).strip()

if RENDER_EXTERNAL_HOSTNAME:
    if RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

    render_origin = f'https://{RENDER_EXTERNAL_HOSTNAME}'

    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)


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
# sqlite   = قاعدة بيانات التطوير
# postgres = قاعدة بيانات الإنتاج على Render

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
                'dpg-d9iu2r71dkcs73bgc3hg-a',
            ),

            'PORT': os.getenv(
                'POSTGRES_PORT',
                '5432',
            ),

            # الاحتفاظ باتصالات قاعدة البيانات
            # لتحسين الأداء في الإنتاج
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
        }
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
        }
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

MEDIA_ROOT = BASE_DIR / 'media'


# ==========================================
# إعدادات تسجيل الدخول والخروج
# ==========================================

LOGIN_URL = 'accounts:login'

LOGIN_REDIRECT_URL = '/'

LOGOUT_REDIRECT_URL = 'accounts:login'


# ==========================================
# إعدادات الأمان الخاصة بالإنتاج
# ==========================================

# تعمل هذه الإعدادات عندما يكون DEBUG=False

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

SECURE_HSTS_INCLUDE_SUBDOMAINS = get_boolean_env(
    'SECURE_HSTS_INCLUDE_SUBDOMAINS',
    False,
)

SECURE_HSTS_PRELOAD = get_boolean_env(
    'SECURE_HSTS_PRELOAD',
    False,
)


# Render يرسل البروتوكول الحقيقي في هذا الرأس
SECURE_PROXY_SSL_HEADER = (
    'HTTP_X_FORWARDED_PROTO',
    'https',
)


# ==========================================
# إعدادات الجلسات
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
