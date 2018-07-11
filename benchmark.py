# -*- coding:utf-8 -*-
from __future__ import unicode_literals

import os
import sys
import time


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
        response = requests.get("http://47.95.5.22:9000")
        count += 1
        if count % 100 == 0:
            print(count, time.time() - start)


if __name__ == "__main__":
    _measure()
