# -*- coding: utf-8 -*-

import os
import re
import json
import random
import logging
import datetime
import requests
import magic

from flask import Flask, request, send_file, render_template, make_response, \
                send_from_directory, current_app, session, url_for

from htmlmin.main import minify
from html.parser import HTMLParser
from io import StringIO

from werkzeug.middleware.proxy_fix import ProxyFix

from .extensions import cors, cache, mail
from .config import config as env_config

from flask_mail import Message

app = Flask(
        __name__, 
        template_folder="templates",
        static_folder="static"
    )


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()
    

def strip_tags(html):
    s = MLStripper()
    if not isinstance(html, (bytes, str)):
        html = str(html)
    s.feed(html)
    return s.get_data()


def pretty_date(dt, default=None):
    # Returns string representing "time since" eg 3 days ago, 5 hours ago etc.

    if default is None:
        default = 'adesso'

    now = datetime.datetime.now(datetime.timezone.utc)
    diff = now - dt

    periods = (
        (diff.days / 365, 'anno', 'anni'),
        (diff.days / 30, 'mese', 'mesi'),
        (diff.days / 7, 'settimana', 'settimane'),
        (diff.days, 'giorno', 'giorni'),
        (diff.seconds / 3600, 'ora', 'ore'),
        (diff.seconds / 60, 'minuto', 'minuti'),
        (diff.seconds, 'secondo', 'secondi'),
    )

    for period, singular, plural in periods:

        if not period:
            continue

        if int(period) >= 1:
            if int(period) > 1:
                return u'%d %s fa' % (period, plural)
            return u'%d %s fa' % (period, singular)

    return default


def init_app():
    configure_app(app, env_config)
    return app


def configure_app(app, config=None, blueprints=None):
    configure_app_config(app, config)
    configure_hook(app)
    configure_extensions(app)
    configure_logging(app)
    configure_template_filters(app)
    configure_error_handlers(app)

    return app


def configure_app_config(app, forced_config=None):
    # Load config from default object
    app.config.from_object(env_config)

    if forced_config and isinstance(forced_config, object):
        app.config.from_object(forced_config)


def configure_hook(app):
    @app.before_request
    def before_request():
        pass
    
    @app.after_request
    def response_minify(response):
        """
        minify html response to decrease site traffic
        """
        if response.content_type == u'text/html; charset=utf-8' and env_config.APPLICATION_ENV == 'production':
            response.set_data(
                minify(response.get_data(as_text=True))
            )

            return response
        return response


def configure_extensions(app):
    # Make app work with proxies (like nginx) that set proxy headers.
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # Initialize Flask-CORS
    cors.init_app(app, supports_credentials=True)
    # cors.init_app(app, supports_credentials=True, resources={r"/*": {"origins": "*"}})

    # Initialize Flask-Mail
    mail.init_app(app)

    # Initialize Flask-Cache
    cache.init_app(app)


def configure_logging(app):
    # Configure logging
    
    #logging.config.dictConfig(app.config.get('LOGGING'))
    logging.basicConfig(level=logging.DEBUG)
    #logging.getLogger(__name__)

    if app.debug:
        # Skip debug and test mode. Better check terminal output.
        return

    # TODO: production loggers for (info, email, etc)


def configure_template_filters(app):  # sourcery skip: none-compare
    
    app.jinja_env.add_extension('jinja2.ext.do')

    @app.template_filter()
    def readable_size(value, suffix="b"):
        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
            if abs(value) < 1024.0:
                return f"{value:3.1f} {unit}{suffix}"
            value /= 1024.0
        return f"{value:.1f} Yi{suffix}"

    app.jinja_env.globals.update(readable_size=readable_size)

    @app.template_filter()
    def parent_path(value):
        return "/".join(value.split('/')[:-1]) if value else ''

    app.jinja_env.globals.update(parent_path=parent_path)

    @app.template_filter()
    def summarize_suffix(value, max_chars=30):
        if not value:
            return ''
        if len(value) <= max_chars:
            return value
        elif len(value) - max_chars <= max_chars:
            return f"...{value[(len(value) - max_chars):].lstrip()}"
        else:
            return f"...{value[max_chars:].lstrip()}"

    app.jinja_env.globals.update(summarize_suffix=summarize_suffix)

    @app.template_filter()
    def summarize(value, max_chars=30):
        if not value:
            return ''
        return value if len(value) <= max_chars else f"{value[:max_chars].rstrip()}..."

    app.jinja_env.globals.update(summarize=summarize)

    @app.template_filter()
    def microseconds_to_datetime(value):
        if not value:
            return ''
        return datetime.datetime(1601, 1, 1, tzinfo=env_config.TIMEZONE) + datetime.timedelta(microseconds=int(value))

    app.jinja_env.globals.update(microseconds_to_datetime=microseconds_to_datetime)

    @app.template_filter()
    def timestamp_to_datetime(value):
        if not value:
            return ''
        return datetime.datetime.fromtimestamp(value).strftime(env_config.DATE_TIME_FORMAT)

    app.jinja_env.globals.update(timestamp_to_datetime=timestamp_to_datetime)

    @app.template_filter()
    def _pretty_date(value):
        if not value:
            return ''
        return pretty_date(value)

    app.jinja_env.globals.update(_pretty_date=_pretty_date)

    @app.template_filter()
    def format_date(value, format=env_config.DATE_FORMAT):
        if not value:
            return ''
        return value.strftime(format)

    @app.template_filter()
    def format_datetime(value, format=env_config.DATE_TIME_FORMAT):
        if not value:
            return ''
        return value.strftime(format)

    app.jinja_env.globals.update(format_datetime=format_datetime)

    @app.template_filter()
    def config_var(value=None):
        if not value:
            return ''
        return current_app.config[value]

    app.jinja_env.globals.update(config_var=config_var)

    @app.template_filter()
    def camelize(value):
        if not value:
            return ''
        return ''.join(x.capitalize() or '_' for x in value.split('_'))

    app.jinja_env.globals.update(camelize=camelize)

    @app.template_filter()
    def camelize_with_spaces(value):
        if not value:
            return ''
        return ''.join(f'{x.capitalize()} ' or '_' for x in value.split('_'))

    app.jinja_env.globals.update(camelize_with_spaces=camelize_with_spaces)

    @app.template_filter()
    def camelize_label_with_spaces(value):
        if not value:
            return ''
        return ''.join(
            f'{x.capitalize()} ' or '_'
            for x in var_name_to_string(value).split(' ')
        )

    app.jinja_env.globals.update(camelize_label_with_spaces=camelize_label_with_spaces)

    @app.template_filter()
    def random_filename(value, start=0, end=100000, extension='', prefix='', suffix='', path=''):
        number = random.randrange(start, end)
        return f'{path}{prefix}{number}{suffix}{extension}'

    app.jinja_env.globals.update(random_filename=random_filename)

    @app.template_filter()
    def var_name_to_string(value):
        if not value:
            return ''
        words = []
        for y in re.findall('[a-zA-Z][^A-Z]*', value):
            tmp = y.split('_')
            for x in tmp:
                words.extend(x.split('-')) 
        return ' '.join(words)

    app.jinja_env.globals.update(var_name_to_string=var_name_to_string)

    @app.template_filter()
    def strip_html(value):
        if not value:
            return ''
        return strip_tags(value)

    app.jinja_env.globals.update(strip_html=strip_html)

    @app.template_filter()
    def strip_model_name(value):
        if not value:
            return ''
        return ''.join(value.split('.')[1:])

    app.jinja_env.globals.update(strip_model_name=strip_model_name)

    @app.template_filter()
    def to_int(value, default=''):
        if not value:
            return '' if default == '' else 0
        return int(value)

    app.jinja_env.globals.update(to_int=to_int)

    @app.template_filter()
    def to_str(value):
        if not value:
            return ''
        return str(value)

    app.jinja_env.globals.update(to_str=to_str)

    @app.template_filter()
    def to_unicode(value):
        if not value:
            return ''
        return value.__unicode__()

    app.jinja_env.globals.update(to_unicode=to_unicode)

    @app.template_filter()
    def to_dict(value):
        if not value:
            return ''
        return dict(value)

    app.jinja_env.globals.update(to_dict=to_dict)

    @app.template_filter()
    def to_list(value):
        if not value:
            return ''
        return list(value)

    app.jinja_env.globals.update(to_list=to_list)

    @app.template_filter()
    def _json(value):
        return json.dumps(value)

    app.jinja_env.globals.update(json=_json)

    @app.template_filter()
    def basename(value):
        if not value:
            return ''
        return os.path.basename(value)

    app.jinja_env.globals.update(basename=basename)

    @app.template_filter()
    def dirname(value):
        if not value:
            return ''
        return os.path.dirname(value)

    app.jinja_env.globals.update(dirname=dirname)

    @app.context_processor
    def inject():
        global_dict = {
            'now': datetime.datetime.now(datetime.timezone.utc),
            'current_url': request.url_rule.endpoint if request.url_rule else '',
            'current_date': datetime.datetime.now(),
            'config': env_config,
            'application_env': env_config.APPLICATION_ENV,
            'session': session,
            'request': request,
            'get_url': url_for,
            'check_ip_string': [str(octet[0]) for octet in request.remote_addr.split('.')],
            'ADMIN_URL_PREFIX': env_config.ADMIN_URL_PREFIX,
            'BASE_URL': env_config.BASE_URL,
            'STATIC_URL': env_config.STATIC_URL,
            'URLS': env_config.URLS,
            'TIMEZONE': env_config.TIMEZONE,
            'DATE_TIME_FORMAT': env_config.DATE_TIME_FORMAT,
            'DATE_FORMAT': env_config.DATE_FORMAT,
            'APPLICATION_PATH': env_config.APPLICATION_PATH,
            'INSTANCE_FOLDER_PATH': env_config.INSTANCE_FOLDER_PATH,
            'BASE_PATH': env_config.BASE_PATH,
            'STATIC_PATH': env_config.STATIC_PATH,
            'STATIC_IMAGES_PATH': env_config.STATIC_IMAGES_PATH,
            'PATHS': env_config.PATHS,
        }

        return global_dict
    


def configure_error_handlers(app):

    @app.errorhandler(403)
    def forbidden_page(error):
        return (
            ("Oops! You don't have permission to access this page.", 403)
            if request.is_json
            else (render_template('http_statuses/403.html'), 403)
        )

    @app.errorhandler(404)
    def page_not_found(error):
        return (
            ("Ooops! Page not found.", 404)
            if request.is_json
            else (render_template('http_statuses/404.html'), 404)
        )

    @app.errorhandler(500)
    def server_error_page(error):
        return (
            ("Oops! Internal server error. Please try after sometime.", 500)
            if request.is_json
            else (render_template('http_statuses/500.html'), 500)
        )

"""
 *
 *  VIEW HANDLERS
 *
"""

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(env_config.BASE_PATH, 'images'),
                'favicon.ico',mimetype='image/vnd.microsoft.icon')

@app.route("/", methods=["GET", "POST"], defaults={'path': "index.html"})
@app.route("/<path:path>", methods=["GET", "POST"])
def template_render_path(path):
    error_code = 0
    error_msg = ""
    if request.method == "POST" and request.form['form-name'] == 'mail-contact-form':
        def is_valid():
            try:
                if env_config.EMAIL_SEND and env_config.APPLICATION_ENV == 'production':
                    url = 'https://www.google.com/recaptcha/api/siteverify'
                    data = {
                        'secret': env_config.RECAPTCHA_V3_SECRET_KEY,
                        'response': request.form['g-recaptcha-response'],
                        'remoteip': request.remote_addr
                    }
                    headers = {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                    response = requests.post(url, data=data, headers=headers)
                    result = response.json()
                return ( env_config.EMAIL_SEND and env_config.APPLICATION_ENV == 'production' and result['success'] and sum(
                    int(octet[0])
                    for octet in request.remote_addr.split('.')
                ) == int(request.form['check']) ) or ( sum(
                    int(octet[0])
                    for octet in request.remote_addr.split('.')
                ) == int(request.form['check']) )
            except Exception:
                return False

        if is_valid():
            try:
                if env_config.EMAIL_SEND:
                    msg = Message(
                        'Website message: ' + request.form['subject'],
                        sender=(env_config.WEBSITE, env_config.EMAIL_SENDER),
                        recipients=[(env_config.EMAIL_DEST, env_config.EMAIL_DEST_NAME)]
                    )
                    msg.body = f'IP:{request.remote_addr}' + '\n\n' + request.form['message']
                    mail.send(msg)
            except Exception as e:
                error_code = 1
                error_msg = str(e)
        else:
            error_code = 2
            error_msg = "Robot check validation failed."

    paths = [
        f'{env_config.TEMPLATES_PATH}{os.sep}{path}',
        f'{env_config.TEMPLATES_PATH}{os.sep}{path}.htm',
        f'{env_config.TEMPLATES_PATH}{os.sep}{path}.html',
        f'{env_config.STATIC_TEMPLATES_PATH}{os.sep}{path}',
        f'{env_config.STATIC_TEMPLATES_PATH}{os.sep}{path}.htm',
        f'{env_config.STATIC_TEMPLATES_PATH}{os.sep}{path}.html',
    ]

    for path in paths:
        if os.path.exists(path):
            mime = magic.Magic(mime=True)
            mime_type = mime.from_file(path)

            if mime_type:
                if path.startswith(env_config.TEMPLATES_PATH):
                    response = make_response(render_template(path[len(env_config.TEMPLATES_PATH)+1:], error_code=error_code, error_msg=error_msg))
                    response.headers['Content-Type'] = mime_type
                    return response
                else:
                    return send_file(path, mimetype=mime_type)
            else:
                return "MIME type not supported for this file."

    return "Not found"
