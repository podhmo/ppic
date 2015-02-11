# -*- coding:utf-8 -*-
import unittest
from evilunit import test_function
from unittest import mock


def _make_request(name):
    from ppic import Request
    return Request(name=name, previous_version=None)


@test_function("ppic:get_info_from_request")
class Tests(unittest.TestCase):
    def test_success(self):
        with mock.patch("ppic.urlopen_json", autspec=True) as m:
            m.return_value = {}

            request = _make_request("foo")
            result = self._callFUT(request)

            self.assertTrue(result.is_success())
            self.assertEqual(result.name, "foo")

    def test_failure(self):
        with mock.patch("ppic.urlopen_json", autospec=True) as m:
            from ppic.compat import HTTPError
            m.side_effect = HTTPError(404, "not found", None, None, None)

            request = _make_request("foo")
            result = self._callFUT(request)

            self.assertFalse(result.is_success())
            self.assertEqual(result.name, "foo")
