# -*- coding:utf-8 -*-
import time
import json
import contextlib
from . import logger
from .compat import urlopen_json, HTTPError


class PYPIJSONResource(object):
    """access url return json"""
    urlfmt = "https://pypi.python.org/pypi/{name}/json"

    def __init__(self, delay_time):
        self.delay_time = delay_time

    def access(self, request):
        try:
            url = self.urlfmt.format(name=request.name)
            logger.debug("access: url=%s", url)
            time.sleep(self.delay_time)  # delay for pypi server
            return urlopen_json(url), True
        except HTTPError as e:
            return str(e), False

    @contextlib.contextmanager
    def using(self):
        yield self


class CachedResourceWrapper(object):
    def __init__(self, resource, cachepath, timeout):
        self.resource = resource
        self.cachepath = cachepath
        self.timeout = timeout
        self._cache = None

    @contextlib.contextmanager
    def using(self):
        yield self
        if self._cache is not None:
            self.save(self.cachepath)

    def load(self, cachepath):
        try:
            logger.info("load: cachepath=%s", cachepath)
            with open(cachepath, "r") as r:
                self._cache = json.load(r)
        except Exception as e:
            logger.exception("%s", e)
            self._cache = {}

    def save(self, cachepath):
        logger.info("save: cachepath=%s", cachepath)
        with open(cachepath, "w") as w:
            w.write(json.dumps(self._cache))

    @property
    def cache(self):
        if self._cache is not None:
            return self._cache
        self.load(self.cachepath)
        return self._cache

    def access(self, request):
        try:
            value, timestamp = self.cache[request.name]
            if time.time() - timestamp > self.timeout:
                raise KeyError(request.name)
            return value
        except KeyError:
            value = self.resource.access(request)
            self._cache[request.name] = (value, int(time.time()))
            return value
