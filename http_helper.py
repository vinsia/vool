# -*- coding:utf-8 -*-
from __future__ import unicode_literals

from io import BytesIO


class RawRequest:

    def __init__(self):
        self.data = None
        self.header = None
        self.version = None
        self.method = None
        self.url = None
        self._path = None
        self._query_str = None

    @property
    def path(self):
        if self._path:
            return self._path

        self._path, self._query_str = self.url.split("?") if "?" in self.url else (self.url, "")
        return self._path

    @property
    def query_str(self):
        if self._query_str:
            return self._query_str

        self._path, self._query_str = self.url.split("?") if "?" in self.url else (self.url, "")
        return self._query_str

    @staticmethod
    def parse(string_io):
        # state = 0|1|2 分别表示请求行、请求头部、请求数据
        request = RawRequest()
        state = 0
        request.header = {}
        request.data = None
        while True:
            s = string_io.readline()
            s = s.rstrip("\r\n")

            if state == 0:
                request.method, request.url, request.version = s.split(" ")
                state = 1
            elif state == 1:
                index = s.find(":")
                if index > 0:
                    key, value = s[:index], s[index + 1:].strip()
                    request.header[key] = value
                else:
                    state = 2
            elif state == 2:
                request.data = BytesIO(s.encode("utf-8"))
                break
        return request

    def __str__(self):
        return """
            ============
            %s %s %s
            ===header===
            %s
            ====data====
            %s
        """ % (self.method, self.url, self.version, self.header, self.data)
