# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import asyncio
import re
import threading
import time

import uvloop

from http_helper import RawRequest
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
def hello(request):
    msg = "hello %s" % (request.get.get("id"))
    msg += " last_id: %s" % (request.session.get("last_id", None))
    request.session["last_id"] = request.get.get("id", None)
    return 200, msg


@route("/hello/{name}")
def hello_id(request, name):
    return 200, "hello %s %s" % (name, request.get.get("id"))


class Request(threading.local):
    def __init__(self):
        pass

    def bind(self, environ, session):
        self._environ = environ
        self._raw_request = RawRequest.parse(environ["wsgi.input"])
        self._GET = None
        self._POST = None
        self._PARAMS = None
        self._COOKIES = None
        self._SESSION = session

    @staticmethod
    def parse_query_str(query_str):
        r = {}
        for pair in query_str.split("&"):
            try:
                k, v = pair.split("=")
                r[k] = v
            except:
                pass

        return r

    @property
    def session(self):
        return self._SESSION.get(self.cookies.get("sessionid"))

    @property
    def get(self):
        if self._GET:
            return self._GET
        self._GET = Request.parse_query_str(self._environ["QUERY_STRING"])
        return self._GET

    @property
    def post(self):
        if self._POST:
            return self._POST

    @property
    def cookies(self):
        if self._COOKIES:
            return self._COOKIES

        raw_cookie = self._raw_request.header.get("cookie")
        self._COOKIES = {}
        if raw_cookie:
            for cookie_str in raw_cookie.split(";"):
                key, value = cookie_str.split("=")
                key = key.lstrip()
                value = value.rstrip()
                self._COOKIES[key] = value

        return self._COOKIES


class Session(threading.local):
    def __init__(self):
        self._data = {}

    def set(self, key, value):
        self._data[key] = value

    def get(self, key):
        return self._data.setdefault(key, {})


class Vool:
    route_manager = Route()
    request = Request()
    session = Session()

    def application(self, environ, start_response):
        path = environ.get("PATH_INFO")
        method = environ.get("REQUEST_METHOD")
        handler, kwargs = self.route_manager.get_handler(path, method)
        self.request.bind(environ, self.session)
        # 如果request 没有cookie 要给response赛一个cookies
        response_header = {}
        if "sessionid" not in self.request.cookies:
            response_header = [("Set-Cookie", "sessionid=%s" % (int(time.time())))]

        status, response = handler(self.request, **kwargs)
        start_response(status, response_header)
        return iter([response.encode("utf-8")])


if __name__ == "__main__":
    vool = Vool()
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()
    server = WSGIServer(vool.application)
    f = asyncio.start_server(server.accept_client, port=9000, loop=loop)
    server = loop.run_until_complete(f)
    loop.run_forever()
