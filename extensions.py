# -*- coding: utf-8 -*-

from flask_mail import Mail
from flask_caching import Cache
from flask_cors import CORS

cors = CORS()

mail = Mail()

cache = Cache()