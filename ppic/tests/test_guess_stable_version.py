# -*- coding:utf-8 -*-
import unittest
from evilunit import test_target, parameterized


@test_target("ppic:SuccessInfo")
class Tests(unittest.TestCase):
    @parameterized([
        (["1.8", "1.7"], "1.8"),
        (["1.8a", "1.7"], "1.7"),
        (["2.22", "2.9.2"], "2.22"),
        (["12.1", "9.1"], "12.1"),
        (["1.22", "1.7"], "1.22"),
        (["1.8a1", "1.7"], "1.7"),
        (["1.8b1b", "1.7"], "1.7"),
        (["1.8_alpha", "1.7"], "1.7"),
        (["2.alpha", "1.7"], "1.7"),
    ])
    def _test_it(self, candidates, expected):
        target = self._makeOne()
        result = target._guess_stable_version(candidates)
        self.assertEqual(result, expected)

    def _makeOne(self):
        class request:
            name = "foo"
        return self._getTarget()(request, None, None)
