# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import asyncio
import re

import uvloop

from wsgi import WSGIServer


# TODO: 路由可以做的更加丰富一点
class Route(object):
    _route = None
    simple = {}
    complex = {}

    def __new__(cls, *args, **kwargs):
        if cls._route is None:
            cls._route = super().__new__(cls)
        return cls._route

    def get_handler(self, path, method):
        if path in self.simple.get(method, {}):
            return self.simple[method][path], {}

        print(self.complex)
        for pattern, handler in self.complex.get(method, []):
            match = pattern.match(path)
            if match:
                return handler, match.groupdict()

    def compile_route(self, path):
        path = re.sub(r"\{(\w+)\}", r'(?P<\1>\w+)', path)
        return re.compile('^%s$' % path)

    def add_route(self, path, method, handler):
        # 去掉左边的/
        match = re.match(r"^/(\w+/)*\w+$", path)
        if match:
            self.simple.setdefault(method, {})[path] = handler
        else:
            match = self.compile_route(path)
            self.complex.setdefault(method, []).append((match, handler))


def route(path, method="GET"):
    """
    /index
    /{id}/{abc}
    :param method:
    :param path:
    :return:
    """

    def decorator(fn):
        r = Route()
        r.add_route(path, method, fn)

    return decorator


@route("/hello")
def hello():
    return 200, "hello"


@route("/hello/{name}")
def hello_id(name):
    return 200, "hello %s" % (name)


class Vool:
    route_manager = Route()

    def application(self, environ, start_response):
        path = environ.get("PATH_INFO")
        method = environ.get("REQUEST_METHOD")
        handler, kwargs = self.route_manager.get_handler(path, method)
        status, response = handler(**kwargs)
        start_response(status, {})
        return iter([response.encode("utf-8")])


if __name__ == "__main__":
    vool = Vool()
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()
    server = WSGIServer(vool.application)
    f = asyncio.start_server(server.accept_client, port=9000, loop=loop)
    server = loop.run_until_complete(f)
    loop.run_forever()
