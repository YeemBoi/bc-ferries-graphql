"""
For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os
import itertools
from pathlib import Path


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'definitely a very secret default')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'django_filters',
    'graphene_django',
    'django_extensions',
    'sitemap',
    'core',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

AUTHENTICATION_BACKENDS = [
    'graphql_jwt.backends.JSONWebTokenBackend',
    'django.contrib.auth.backends.ModelBackend',
]

ROOT_URLCONF = 'ferries.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ferries.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

CORS_ALLOW_ALL_ORIGINS = DEBUG

GRAPHENE = {
    'SCHEMA': 'ferries.schema.schema',
    'RELAY_CONNECTION_MAX_LIMIT': 250,
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# See http://bcferries.com/robots.txt
SCRAPER_PAUSE_SECS = 10
if DEBUG:
    SCRAPER_PAUSE_SECS = 6

SCRAPER_URL_PREFIX            = 'http://www.bcferries.com'
SCRAPER_SCHEDULES_URL         = SCRAPER_URL_PREFIX + '/routes-fares/schedules'
SCRAPER_CONDITIONS_URL        = SCRAPER_URL_PREFIX + '/current-conditions'
SCRAPER_DEPARTURES_URL        = SCRAPER_URL_PREFIX + '/current-conditions/departures'
SCRAPER_ROUTES_URL            = SCRAPER_URL_PREFIX + '/route-info'
SCRAPER_CC_ROUTES_URL         = SCRAPER_URL_PREFIX + '/cc-route-info'
SCRAPER_FLEET_URL             = SCRAPER_URL_PREFIX + '/on-the-ferry/our-fleet?page={}'
SCRAPER_SCHEDULE_SEASONAL_URL = SCRAPER_URL_PREFIX + '/routes-fares/schedules/seasonal/{}-{}'
SCRAPER_SCHEDULE_DAILY_URL    = SCRAPER_URL_PREFIX + '/routes-fares/schedules/daily/{}-{}'
SCRAPER_SCHEDULE_URL          = SCRAPER_URL_PREFIX + '/getDepartureDates?origin={}&destination={}&selectedMonth=8&selectedYear={}'
SCRAPER_FLEET_PAGE_RANGE      = 2

SCRAPER_MISC_SCHEDULE_URLS = [
    SCRAPER_URL_PREFIX + '/routes-fares/schedules/southern-gulf-islands',
    # SCRAPER_URL_PREFIX + '/routes-fares/schedules/gambier-keats',
]

# How many days into the future to attempt to create schedules for
SCRAPER_FALLBACK_DATE_PERIODS = 100

# BC Ferries doesn't use alt tags on all images, so map image src to amenities
SCRAPER_AMENITY_IMAGE_PATHS = {
    '/web_image/h8e/h8d/8800764362782.jpg': 'Arbutus Coffee Bar',
    '/web_image/h81/h88/8798826168350.jpg': 'Aurora Lounge',
    '/web_image/h03/h6d/8798746312734.jpg': 'Canoe Cafe',
    '/web_image/h41/hd5/8798823022622.jpg': 'Coast Cafe Express',
    '/web_image/hcb/hd0/8798832164894.jpg': 'Coastal Cafe',
    '/web_image/h9d/h69/8800604258334.jpg': 'Pacific Buffet',
    '/web_image/haa/hf3/8800605044766.jpg': 'Passages',
    '/web_image/h20/h0b/8798760566814.jpg': 'SeaWest Lounge',
    '/web_image/h44/h77/8798814371870.jpg': 'Sitka Coffee Place',
    '/web_image/hf7/hb3/8798767808542.jpg': 'The Raven Lounge',
    '/web_image/h6a/h96/8798810800158.jpg': 'Vista Restaurant',
}

# Used by init_scraped_data script
SCRAPER_SCRIPTS = [
    'save_sitemap',
    'scrape_routes',
    'scrape_fleet',
    'scrape_schedule',
]

DEFAULT_STRING_LOOKUPS = ['exact', 'iexact', 'regex', 'icontains', 'istartswith']
DEFAULT_RANGE_LOOKUPS  = ['exact', 'gt', 'lt', 'gte', 'lte']

_use_default_range_lookups = lambda dt : [f'{dt}__{lookup}' for lookup in DEFAULT_RANGE_LOOKUPS]
_use_unnested_range_lookups = lambda lt : itertools.chain(*[_use_default_range_lookups(lookupType) for lookupType in lt])

_DEFAULT_DATE_LOOKUP_TYPES = ['year', 'iso_year', 'month', 'day', 'week', 'week_day', 'iso_week_day', 'quarter']
_DEFAULT_TIME_LOOKUP_TYPES = ['hour', 'minute', 'second']

DEFAULT_DATE_LOOKUPS = [
    *DEFAULT_RANGE_LOOKUPS,
    *_use_unnested_range_lookups(_DEFAULT_DATE_LOOKUP_TYPES),
]
DEFAULT_TIME_LOOKUPS = [
    *DEFAULT_RANGE_LOOKUPS,
    *_use_unnested_range_lookups(_DEFAULT_TIME_LOOKUP_TYPES),
]
DEFAULT_DATETIME_LOOKUPS = [
    *DEFAULT_RANGE_LOOKUPS,
    *_use_default_range_lookups('date'),
    *_use_unnested_range_lookups(_DEFAULT_DATE_LOOKUP_TYPES),
    *_use_default_range_lookups('time'),
    *_use_unnested_range_lookups(_DEFAULT_TIME_LOOKUP_TYPES),
]
