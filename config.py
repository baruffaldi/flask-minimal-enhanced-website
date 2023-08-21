from datetime import timedelta
from os import environ, path
import secrets
import ast

from .constants import *


class AttributeDict(dict):
    def __getattr__(self, key):
        if key in self:
            return self[key]
        else:
            raise AttributeError(f"'AttributeDict' object has no attribute '{key}'")

    def __setattr__(self, key, value):
        self[key] = value


class BaseConfig(object):
    ''' Base config class. '''
    
    """
    SERVER_NAME = None
    PROPAGATE_EXCEPTIONS = None
    PRESERVE_CONTEXT_ON_EXCEPTION = None
    PERMANENT_SESSION_LIFETIME = timedelta(days=31)
    USE_X_SENDFILE = False
    SESSION_COOKIE_NAME = "session"
    SESSION_COOKIE_DOMAIN = None
    SESSION_COOKIE_PATH = None
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = None
    SESSION_REFRESH_EACH_REQUEST = True
    MAX_CONTENT_LENGTH = None
    SEND_FILE_MAX_AGE_DEFAULT = None
    TRAP_BAD_REQUEST_ERRORS = None
    TRAP_HTTP_EXCEPTIONS = False
    EXPLAIN_TEMPLATE_LOADING = False
    PREFERRED_URL_SCHEME = "http"
    JSON_AS_ASCII = True
    JSON_SORT_KEYS = True
    JSONIFY_PRETTYPRINT_REGULAR = True
    JSONIFY_MIMETYPE = "application/json"
    TEMPLATES_AUTO_RELOAD = None
    MAX_COOKIE_SIZE = 4093
    """

    ENV = None

    DEBUG = True
    TESTING = True
    
    HOST = "127.0.0.1"
    PORT = 80

    APP_NAME = 'flask'

    PROJECT = "portale"
    PROJECT_NAME = "Portale"
    PROJECT_ROOT = BASE_PATH
    PROJECT_APP_ROOT = path.join(BASE_PATH, 'portale')
    APPLICATION_ROOT = '/' #PROJECT_APP_ROOT # "/"

    ORIGINS = ['*']

    EMAIL_CHARSET = 'UTF-8'
    
    SECRET_KEY = secrets.token_urlsafe()

    LOG_INFO_FILE = path.join(BASE_PATH, 'log', 'info.log')
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '[%(asctime)s] - %(name)s - %(levelname)s - '
                '%(message)s',
                'datefmt': '%b %d %Y %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s - %(message)s'
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'simple'
            },
            'log_info_file': {
                'level': 'DEBUG',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': LOG_INFO_FILE,
                'maxBytes': 16777216,  # 16megabytes
                'formatter': 'standard',
                'backupCount': 5
            },
        },
        'loggers': {
            APP_NAME: {
                'level': 'DEBUG',
                'handlers': ['log_info_file'],
            },
        },
    }

    REMEMBER_COOKIE_SAMESITE = "strict"
    SESSION_COOKIE_SAMESITE = "strict"

    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SQLALCHEMY_RECORD_QUERIES = True

    SECURITY_TOKEN_MAX_AGE=60
    SECURITY_TOKEN_AUTHENTICATION_HEADER="Auth-Token"
    SECURITY_PASSWORD_HASH="bcrypt"
    SECURITY_PASSWORD_SALT="58ed12647fa2942d7743082241f4d17893c44a965198b1e9e245ce4575d324b6"
    SECURITY_REGISTERABLE=True
    SECURITY_CONFIRMABLE=False
    SECURITY_SEND_REGISTER_EMAIL=False
    SECURITY_WEBAUTHN=False
    SECURITY_POST_LOGIN_VIEW = ADMIN_URL_PREFIX
    SECURITY_POST_REGISTER_VIEW = '/post-register'

    WTF_CSRF_ENABLED = False

    CACHE_NO_NULL_WARNING = True

    RANDOM_WALLPAPER_LOGIN = False

    """
    CELERY_BROKER_URL = f'sqla+{SQLALCHEMY_DATABASE_URI}'
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    CELERYBEAT_SCHEDULE = {
        #'example_task': {
        #    'task': 'tasks.example_task',
        #    'schedule': timedelta(seconds=2),
        #    'args': ()
        #},
    }
    """

    #API_KEY = '436236939443955C11494D4484513'
    """BROKER_URL = environ.get('BROKER_URL', 'redis://localhost:6379')
    RESULT_BACKEND = environ.get('RESULT_BACKEND', 'redis://localhost:6379')"""
    # Google OAuth
    """GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "abc123")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "password")
    GOOGLE_REFRESH_TOKEN_URL = "https://www.googleapis.com/oauth2/v4/token"
    GOOGLE_CLIENT_KWARGS = dict(
        scope=" ".join(
            [
                "openid",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/calendar.readonly",
            ]
        )
    )
    GOOGLE_AUTHORIZE_PARAMS = {"access_type": "offline"}
    """

    EMAIL_SEND = False


class Development(BaseConfig):
    ''' Development config. '''

    ENV = 'development'


class Staging(Development):
    ''' Staging config. '''

    ENV = 'staging'

    SECURITY_REGISTERABLE=False

    EMAIL_SEND = True


class Production(Staging):
    ''' Production config '''

    ENV = 'production'

    DEBUG = False
    TESTING = False

    JSONIFY_PRETTYPRINT_REGULAR = False

    SQLALCHEMY_TRACK_MODIFICATIONS=False
    SECURITY_REGISTERABLE=False


configurations = {
    'development': Development,
    'staging': Staging,
    'production': Production,
}

config = configurations[APPLICATION_ENV]

with open('constants.py', 'r') as file:
    content = file.read()

tree = ast.parse(content)

for node in ast.walk(tree):
    if isinstance(node, ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                var_name = target.id
                var_value = None
                if var_name in globals():
                    var_value = globals()[var_name]
                elif var_name in locals():
                    var_value = locals()[var_name]
                setattr(config, var_name, var_value)
