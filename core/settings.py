"""
For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

import os
import itertools
import logging
from pathlib import Path
import dj_database_url
from celery.schedules import crontab


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = (os.environ.get('DEBUG', 'true').lower() == 'true')

# SECURITY WARNING: keep the secret key used in production secret!
if DEBUG:
    SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'definitely a very secret default')
else:
    SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

ALLOWED_HOSTS = [
    'http://localhost',
    'http://127.0.0.1',
    *os.environ.get('ALLOWED_HOSTS', '').split()
]


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
    'ferries',
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

ROOT_URLCONF = 'core.urls'

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

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {}
if DEBUG:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }

else:
    DATABASES['default'] = dj_database_url.config()


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

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-ca'
TIME_ZONE = 'America/Vancouver'
USE_I18N = True
USE_L10N = True
USE_TZ = DATABASES['default']['ENGINE'] == 'django.db.backends.postgresql_psycopg2'

CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    'http://localhost',
    'http://127.0.0.1',
    *os.environ.get('CORS_ALLOWED_ORIGINS', '').split()
]

GRAPHENE = {
    'SCHEMA': 'core.schema.schema',
    'RELAY_CONNECTION_MAX_LIMIT': 250,
    'MIDDLEWARE': [
        'graphql_jwt.middleware.JSONWebTokenMiddleware',
    ],
}
if DEBUG:
    GRAPHENE['MIDDLEWARE'].append('graphene_django.debug.DjangoDebugMiddleware')

CELERY_BROKER_URL           = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND       = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT       = ['application/json']
CELERY_TASK_SERIALIZER      = 'json'
CELERY_RESULT_SERIALIZER    = 'json'
CELERY_TIMEZONE             = TIME_ZONE
CELERY_BEAT_SCHEDULE = {    # Odd timings are in consideration of http://bcferries.com/robots.txt
    'scrape_current_conditions': {
        'task': 'ferries.tasks.scrape_current_conditions_task',
        'schedule': crontab(minute='*/5'),
    },
    'scrape_schedule': {
        'task': 'ferries.tasks.scrape_schedule_task',
        'schedule': crontab(0, 23, day_of_week=1),
    },
    'save_sitemap': {
        'task': 'ferries.tasks.save_sitemap_task',
        'schedule': crontab(0, 21, day_of_week=2),
    },
    'scrape_fleet': {
        'task': 'ferries.tasks.scrape_fleet_task',
        'schedule': crontab(10, 21, day_of_month=2),
    },
    'scrape_routes': {
        'task': 'ferries.tasks.scrape_routes_task',
        'schedule': crontab(0, 21, day_of_month=1, month_of_year='*/2'),
    },
}

from datedelta import datedelta
SCRAPER = {
    'PARSER':               'html5lib',         # used by bs4
    'PAUSE_SECS':           0 if DEBUG else 10, # See http://bcferries.com/robots.txt
    'FALLBACK_DATEDELTA':   datedelta(months=3),# How far into the future to create schedules for, if not automatically determined
    'FLEET_PAGE_RANGE':     2,
    'LOG_LEVEL':            logging.DEBUG,
    'INIT_SCRIPTS': [       # Used by init_scraped_data script
        'save_sitemap',
        'scrape_routes',
        'scrape_fleet',
        'scrape_schedule',
        'scrape_current_conditions',
    ],
    'URL_PREFIX': 'https://www.bcferries.com',
    'URL_PATHS': {
        'SCHEDULES':            '/routes-fares/schedules',
        'CONDITIONS':           '/current-conditions',
        'DEPARTURES':           '/current-conditions/departures',
        'ROUTE_CONDITIONS':     '/current-conditions/{}',
        'ROUTES':               '/route-info',
        'CC_ROUTES':            '/cc-route-info',
        'FLEET':                '/on-the-ferry/our-fleet?page={}',
        'SCHEDULE_SEASONAL':    '/routes-fares/schedules/seasonal/{}',
        'SCHEDULE_DATES':       '/getDepartureDates?origin={}&destination={}&selectedMonth={}&selectedYear={}',
        'DEPARTURES':           '/current-conditions/departures',
        'TERMINAL':             '/travel-boarding/terminal-directions-parking-food/{}/{}',
        'SHIP':                 '/on-the-ferry/our-fleet/{}/{}',
        'SCHEDULES':            '/routes-fares/schedules',
        'MISC_SCHEDULES': [
            '/routes-fares/schedules/southern-gulf-islands',
          # '/routes-fares/schedules/gambier-keats',
        ],
    },
}

_RANGE_LOOKUPS  = ['exact', 'gt', 'lt', 'gte', 'lte']
_use_range_lookups = lambda dt: [f'{dt}__{lookup}' for lookup in _RANGE_LOOKUPS]
_use_unnested_range_lookups = lambda lt: itertools.chain(*[_use_range_lookups(lookupType) for lookupType in lt])
_DATE_LOOKUPS = ['year', 'month', 'day', 'week_day']
_TIME_LOOKUPS = ['hour', 'minute']

from datetime import date, time, datetime, timedelta
DEFAULT_LOOKUPS = {
    str: ['exact', 'iexact', 'regex', 'iregex', 'icontains'],
    bool: ['exact'],
    int: _RANGE_LOOKUPS,
    date: [
        *_RANGE_LOOKUPS,
        *_use_unnested_range_lookups(_DATE_LOOKUPS),
    ],
    time: [
        *_RANGE_LOOKUPS,
        *_use_unnested_range_lookups(_TIME_LOOKUPS),
    ],
    datetime: [
        *_RANGE_LOOKUPS,
        *_use_range_lookups('date'),
        *_use_unnested_range_lookups(_DATE_LOOKUPS),
        *_use_range_lookups('time'),
        *_use_unnested_range_lookups(_TIME_LOOKUPS),
    ],
    timedelta: _RANGE_LOOKUPS,
}
