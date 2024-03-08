import os
from webapp.core.utils import boolenaize 

# Examples:

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '4f6y-r63w9y91)+wx($e!$8l3au@+b0oi7-=)3d$j06x2%r$88')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = booleanize(os.environ.get('DJANGO_DEBUG', False))

# SECURITY WARNING: check if you want this in production
ALLOWED_HOSTS = ['*']

# Static files
STATIC_URL = '/static/'         # URL path
STATIC_ROOT = '/webapp/static'  # Filesystem path


#===============================
#  Logging
#===============================

DJANGO_LOG_LEVEL  = os.environ.get('DJANGO_LOG_LEVEL','ERROR')
WEBAPP_LOG_LEVEL = os.environ.get('WEBAPP_LOG_LEVEL','ERROR')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d '
                      '%(thread)d %(message)s',
        },
        'halfverbose': {
            'format': '%(asctime)s, %(name)s: [%(levelname)s] - %(message)s',
            'datefmt': '%m/%d/%Y %I:%M:%S %p'
        }
    },

    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },

    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'halfverbose',
        },
    },
    'loggers': {
        'webapp': {
            'handlers': ['console'],
            'level': WEBAPP_LOG_LEVEL,
            'propagate': False, # Do not propagate or the root logger will emit as well, and even at lower levels. 
        },
        'django': {
            'handlers': ['console'],
            'level': DJANGO_LOG_LEVEL,
            'propagate': False, # Do not propagate or the root logger will emit as well, and even at lower levels. 
        }, 
        # Read more about the 'django' logger: https://docs.djangoproject.com/en/2.2/topics/logging/#django-logger
        # Read more about logging in the right way: https://lincolnloop.com/blog/django-logging-right-way/
    }
}

