# -*- coding:utf-8 -*-
import unittest
from evilunit import test_function


def _make_request(name):
    from ppic import Request
    return Request(name=name, previous_version=None, distribution=None)


class DummyResource(object):
    def __init__(self, retval):
        self.retval = retval

    def access(self, name):
        return self.retval


@test_function("ppic:get_info_from_request")
class Tests(unittest.TestCase):
    def test_success(self):
        resource = DummyResource(({}, True))
        request = _make_request("foo")
        result = self._callFUT(resource, request)

        self.assertTrue(result.is_success())
        self.assertEqual(result.name, "foo")

    def test_failure(self):
        resource = DummyResource(("not found", False))
        request = _make_request("foo")
        result = self._callFUT(resource, request)

        self.assertFalse(result.is_success())
        self.assertEqual(result.name, "foo")
