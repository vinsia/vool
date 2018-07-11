# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import os
import sys
import time
from multiprocessing import Process

from wsgi import WSGIServer


def daemonize() -> None:
    """Move current process to daemon process."""
    # Create first fork
    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    # Decouple fork
    os.setsid()

    # Create second fork
    pid = os.fork()
    if pid > 0:
        sys.exit(0)

    # redirect standard file descriptors to devnull
    infd = open(os.devnull, 'r')
    outfd = open(os.devnull, 'a+')
    sys.stdout.flush()
    sys.stderr.flush()
    os.dup2(infd.fileno(), sys.stdin.fileno())
    os.dup2(outfd.fileno(), sys.stdout.fileno())
    os.dup2(outfd.fileno(), sys.stderr.fileno())


def _measure():
    count = 0
    start = time.time()
    import requests
    while True:
        response = requests.get("http://127.0.0.1:9000")
        count += 1
        if count % 1000 == 0:
            print(count, time.time() - start)


if __name__ == "__main__":
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
    s_p = Process(target=server.start, args=())
    s_p.start()

    c_p = Process(target=_measure, args=())
    c_p.start()

    s_p.join()
    c_p.join()
