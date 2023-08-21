from gevent.pywsgi import WSGIServer

from . import init_app

app = init_app()


if __name__ == "__main__":
    http_server = WSGIServer(("127.0.0.1", 5000), app)
    http_server.serve_forever()
