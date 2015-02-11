# -*- coding:utf-8 -*-
import sys
import types
import json
# True if we are running on Python 3.
PY3 = sys.version_info[0] == 3


if PY3: # pragma: no cover
    from urllib.error import HTTPError
else:
    HTTPError = Exception

if PY3:
    from urllib.request import urlopen

    def urlopen_json(url):
        return json.loads(urlopen(url).readall().decode("utf-8"))
else:
    from urllib import urlopen

    class HTTPError(Exception):
        pass

    def urlopen_json(url):
        r = urlopen(url)
        if r.code == 200:
            return json.load(r)
        else:
            raise HTTPError("{!r} {}".format(r.code, r.url))
