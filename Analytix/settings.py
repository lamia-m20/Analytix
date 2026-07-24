from pathlib import Path


# المسار الرئيسي للمشروع
BASE_DIR = Path(__file__).resolve().parent.parent


# إعدادات الأمان
SECRET_KEY = 'django-insecure-oo^3l@l^3e_=7*#^y(p9@^0_j(1ri3w8fzj+kkcp&3=g#_&&3v'

DEBUG = True

ALLOWED_HOSTS = []


# التطبيقات المثبتة
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



# الوسائط البرمجية
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


# ملف الروابط الرئيسي
ROOT_URLCONF = 'Analytix.urls'


# إعدادات القوالب
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            BASE_DIR / 'templates',
        ],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


# إعدادات WSGI
WSGI_APPLICATION = 'Analytix.wsgi.application'


# قاعدة البيانات
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# التحقق من كلمات المرور
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


# اللغة العربية
LANGUAGE_CODE = 'ar'

# توقيت مدينة الرياض
TIME_ZONE = 'Asia/Riyadh'

# تفعيل الترجمة
USE_I18N = True

# استخدام التوقيت الزمني
USE_TZ = True

# الملفات الثابتة
STATIC_URL = 'static/'

# نوع المفتاح الافتراضي للنماذج
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'