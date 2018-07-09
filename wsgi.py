# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import socket
import sys
from io import StringIO

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
        WSGIServer.server_port = port
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
            response = 'HTTP/1.1 {status}\r\n'.format(status=self.status)
            for header in self.response_headers:
                response += '{0}: {1}\r\n'.format(*header)
            response += '\r\n'
            response += result
            client_connection.sendall(bytes(response, encoding="utf-8"))
        finally:
            client_connection.close()

    def parse_data(self):
        data = self.raw_data.decode("utf-8")
        format_data = data.splitlines()

        print(format_data)
        # 第一行为 'method path version'
        method, url, http_version = format_data[0].split()
        path, query_str = WSGIServer.parse_parameter(url)
        environ = {
            "REQUEST_METHOD": method,
            # "SCRIPT_NAME": "",
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
            return path, {}

        path, parameter_str = path.split("?")
        return path, parameter_str
        # parameter = {}
        # parameter_str = parameter_str.lstrip("?")
        # for parameter_s in parameter_str.split("&"):
        #     key, value = parameter_s.split("=")
        #     parameter[key] = value
        # return path, parameter


if __name__ == "__main__":
    def application(environ, start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        return "<h1>Hello, web!</h1>"


    server = WSGIServer(("0.0.0.0", 9000), application)
    server.serve_forever()