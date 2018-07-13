# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import asyncio
import sys
from io import StringIO

import uvloop

from http_helper import RawRequest


class Response(object):
    def __init__(self):
        self.status = None
        self.response_headers = []
        self.result = None

    def start_response(self, status, response_headers, exc_info=None):
        self.status = status
        self.response_headers = response_headers


def parse_parameter(path):
    if "?" not in path:
        return path, ""

    path, parameter_str = path.split("?")
    return path, parameter_str


class WSGIServer(asyncio.Protocol):
    server_name = "localhost"
    server_port = "80"

    def __init__(self, application):
        self.application = application

    async def accept_client(self, client_reader, client_writer):
        try:
            raw_data = await client_reader.read(1024)
            data = raw_data.decode("utf-8")
            format_data = data.splitlines()

            print(format_data)
            # 第一行为 'method path version'
            request = RawRequest.parse(StringIO(data))
            print(request)
            # method, url, http_version = format_data[0].split() if format_data else ["GET", "/", "http 1.0"]
            # https://www.python.org/dev/peps/pep-0333/#environ-variables
            environ = {
                "REQUEST_METHOD": request.method,
                "SCRIPT_NAME": "",
                "PATH_INFO": request.path,
                "QUERY_STRING": request.query_str,
                "CONTENT_TYPE": "text/plain",
                "SERVER_NAME": WSGIServer.server_name,
                "SERVER_PORT": WSGIServer.server_port,
                "SERVER_PROTOCOL": request.version,
                "wsgi.version": (1, 0),
                "wsgi.url_scheme": "http",
                "wsgi.input": StringIO(data),
                "wsgi.errors": sys.stderr,
                "wsgi.multithread": False,
                "wsgi.multiprocess": False,
                "wsgi.run_once": False,
            }
            response = Response()
            response.result = self.application(environ, response.start_response)
            await self.finish_response(client_writer, response)
        finally:
            await client_writer.drain()
            client_writer.close()

    @staticmethod
    async def finish_response(client_writer, response):
        try:
            # TODO: 是否有更好的处理bytes的方法
            resp = bytes('HTTP/1.1 {status}\r\n'.format(status=response.status), encoding="utf-8")
            for header in response.response_headers:
                resp += bytes('{0}: {1}\r\n'.format(*header), encoding="utf-8")
            resp += bytes('\r\n', encoding="utf-8")
            # result为一个迭代器，而不一定string或者byte
            for data in response.result:
                resp += data
            # 迭代器必须关闭？ 为啥?
            # try:
            #     response.result.close()
            # except:
            #     pass
            client_writer.write(resp)
        except:
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    # @validator
    def application(environ, start_response):
        data = b'Hello, World!\n'
        status = '200 OK'

        response_headers = [
            ('Content-type', 'text/plain'),
            ('Content-Length', str(len(data))),
        ]
        start_response(status, response_headers)
        return iter([data])


    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    loop = asyncio.get_event_loop()
    server = WSGIServer(application)
    f = asyncio.start_server(server.accept_client, port=9000, loop=loop)
    server = loop.run_until_complete(f)
    loop.run_forever()
