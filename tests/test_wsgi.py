# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from wsgi import WSGIServer


def test_wsgi_flask():
    from flask import Flask
    from flask import Response

    flask_app = Flask(__name__)

    @flask_app.route('/hello')
    def hello_world():
        return Response(
            'hello',
            mimetype='text/plain'
        )

    server = WSGIServer(("0.0.0.0", 9000), flask_app.wsgi_app)
    server.serve_forever()
