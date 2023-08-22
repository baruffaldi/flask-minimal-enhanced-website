import pytz

import pathlib
from os import environ, path, makedirs # , getuid, getgid

WEBSITE = environ.get('WEBSITE') or 'www.example.com'
    
MAIL_SERVER = environ.get('MAIL_SERVER') or 'smtp.gmail.com'
MAIL_PORT = environ.get('MAIL_PORT') or 465
MAIL_USERNAME = environ.get('MAIL_USERNAME') or 'blah@rtfm.info'
MAIL_PASSWORD = environ.get('MAIL_PASSWORD') or 'lala'
MAIL_USE_TLS = environ.get('MAIL_USE_TLS') or False
MAIL_USE_SSL = environ.get('MAIL_USE_SSL') or True

RECAPTCHA_V3_SECRET_KEY = environ.get('RECAPTCHA_V3_SECRET_KEY') or 'no-secret-key-set'
RECAPTCHA_V3_PUBLIC_KEY = environ.get('RECAPTCHA_V3_PUBLIC_KEY') or 'no-public-key-set'
EMAIL_SENDER = environ.get('EMAIL_SENDER') or 'spam@rtfm.info'
EMAIL_DEST = environ.get('EMAIL_DEST') or 'filippo+website@rtfm.info'
EMAIL_DEST_NAME = environ.get('EMAIL_DEST_NAME') or 'Filippo Baruffaldi'

APPLICATION_ENV = environ.get('APPLICATION_ENV') or 'development'

TIMEZONE = pytz.timezone('Europe/Rome')
DATE_FORMAT = environ.get('DATE_FORMAT') or '%Y-%m-%d'
TIME_FORMAT = environ.get('TIME_FORMAT') or '%H:%M:%S'
DATE_TIME_FORMAT = environ.get('DATE_TIME_FORMAT') or '%Y-%m-%d %H:%M:%S'
DB_RESULT_DATE_TIME_FORMAT = environ.get('DB_RESULT_DATE_TIME_FORMAT') or '%Y-%m-%dT%H: %M: %S'

# PATHs
APPLICATION_PATH = pathlib.Path(__file__).parent.resolve()
BASE_PATH = path.dirname(path.abspath(__file__))
INSTANCE_FOLDER_PATH = path.abspath(path.join(BASE_PATH, '..'))
STATIC_PATH = path.join(BASE_PATH, 'static')
makedirs(STATIC_PATH, 0o777, exist_ok=True)

TEMPLATES_PATH = path.join(BASE_PATH, 'templates')
makedirs(TEMPLATES_PATH, 0o777, exist_ok=True)

STATIC_TEMPLATES_PATH = path.join(BASE_PATH, 'static-templates')
makedirs(STATIC_TEMPLATES_PATH, 0o777, exist_ok=True)

STATIC_IMAGES_PATH = path.join(STATIC_PATH, 'images')
makedirs(STATIC_IMAGES_PATH, 0o777, exist_ok=True)

PATHS = {
    'APPLICATION_PATH': APPLICATION_PATH,
    'INSTANCE_FOLDER_PATH': INSTANCE_FOLDER_PATH,
    'BASE_PATH': BASE_PATH,
    'STATIC_PATH': STATIC_PATH,
    'STATIC_IMAGES_PATH': STATIC_IMAGES_PATH,
    'TEMPLATES_PATH': TEMPLATES_PATH,
    'STATIC_TEMPLATES_PATH': STATIC_TEMPLATES_PATH,
}

# URLs
BASE_URL = '/'
STATIC_URL = path.join(BASE_URL, 'static')
STATIC_IMAGES_URL = path.join(STATIC_URL, 'images')
ADMIN_URL_PREFIX = ''

URLS = {
    'BASE_URL': BASE_URL,
    'STATIC_URL': STATIC_URL,
    'STATIC_IMAGES_URL': STATIC_IMAGES_URL,
}

#PROCESS_UID = getuid()
#PROCESS_GID = getgid()