# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import socket
import sys
from io import StringIO
from wsgiref.validate import validator

BUFFER_SIZE = 4096


class WSGIServer(object):
    """
    :param address = ("127.0.0.1", 8080)
    """
    server_name = "localhost"
    server_port = "80"

    def __init__(self, address, application):
        self.application = application
        self._socket = sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(address)
        sock.listen(1)

        host, port = sock.getsockname()[:2]
        WSGIServer.server_name = socket.getfqdn(host)
        WSGIServer.server_port = str(port)
        self.raw_data = None
        self.status = 200
        self.response_headers = []

    def serve_forever(self):
        sock = self._socket
        while True:
            client_connection, _ = _sock, addr = sock.accept()
            self.handle_request(client_connection)

    def handle_request(self, client_connection):
        self.raw_data = raw_data = client_connection.recv(BUFFER_SIZE)  # TODO: 要全部输入
        environ = self.parse_data()
        result = self.application(environ, self.start_response)
        self.finish_response(client_connection, result)

    def start_response(self, status, response_headers, exc_info=None):
        self.status = status
        self.response_headers = response_headers

    def finish_response(self, client_connection, result):
        try:
            # TODO: 是否有更好的处理bytes的方法
            response = bytes('HTTP/1.1 {status}\r\n'.format(status=self.status), encoding="utf-8")
            for header in self.response_headers:
                response += bytes('{0}: {1}\r\n'.format(*header), encoding="utf-8")
            response += bytes('\r\n', encoding="utf-8")
            # result为一个迭代器，而不一定string或者byte
            for data in result:
                response += data
            # 迭代器必须关闭？ 为啥?
            result.close()
            client_connection.sendall(response)
        finally:
            client_connection.close()

    def parse_data(self):
        data = self.raw_data.decode("utf-8")
        format_data = data.splitlines()

        print(format_data)
        # 第一行为 'method path version'
        method, url, http_version = format_data[0].split()
        path, query_str = WSGIServer.parse_parameter(url)
        # https://www.python.org/dev/peps/pep-0333/#environ-variables
        environ = {
            "REQUEST_METHOD": method,
            "SCRIPT_NAME": "",
            "PATH_INFO": path,
            "QUERY_STRING": query_str,
            # "CONTENT_TYPE": "text/plain",
            "SERVER_NAME": WSGIServer.server_name,
            "SERVER_PORT": WSGIServer.server_port,
            "SERVER_PROTOCOL": http_version,
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "http",
            "wsgi.input": StringIO(data),
            "wsgi.errors": sys.stderr,
            "wsgi.multithread": False,
            "wsgi.multiprocess": False,
            "wsgi.run_once": False,
        }
        return environ

    @staticmethod
    def parse_parameter(path):
        if "?" not in path:
            return path, ""

        path, parameter_str = path.split("?")
        return path, parameter_str


if __name__ == "__main__":
    @validator
    def application(environ, start_response):
        data = b'Hello, World!\n'
        status = '200 OK'

        response_headers = [
            ('Content-type', 'text/plain'),
            ('Content-Length', str(len(data))),
        ]
        start_response(status, response_headers)
        return iter([data])


    server = WSGIServer(("0.0.0.0", 9000), application)
    server.serve_forever()
