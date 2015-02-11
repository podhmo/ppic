# -*- coding:utf-8 -*-
import unittest
from evilunit import test_function
"""
test
- success[newer]
- success[has updated]
- success[hasnot update(equal)]
- failure
"""


def _make_request(name, previous_version=None):
    from ppic import Request
    return Request(name=name, previous_version=previous_version)


@test_function("ppic:rendering_info_list")
class FailureInfoTests(unittest.TestCase):
    def _make_info(self):
        from ppic import FailureInfo
        return FailureInfo(_make_request("foo"), "404")

    def test_update_candidates(self):
        info = self._make_info()
        result = self._callFUT([info])
        self.assertEqual(result["update_candidates"], [])

    def test_new_install_candidates(self):
        info = self._make_info()
        result = self._callFUT([info])
        self.assertEqual(result["new_install_candidates"], [])


@test_function("ppic:rendering_info_list")
class SuccessInfo__HasUpdate__Tests(unittest.TestCase):
    def _make_info(self):
        from ppic import SuccessInfo
        return SuccessInfo(
            _make_request("foo", previous_version="0.1"),
            {
                "info": {"name": "foo", "version": "0.2"},
                "releases": {"0.2": [{"upload_time": "2014-12-04T23:16:25"}]}
            }
        )

    def test_update_candidates(self):
        info = self._make_info()
        result = self._callFUT([info])
        self.assertEqual(result["update_candidates"], ["foo: '0.1' -> '0.2'"])

    def test_new_install_candidates(self):
        info = self._make_info()
        result = self._callFUT([info])
        self.assertEqual(result["new_install_candidates"], [])


@test_function("ppic:rendering_info_list")
class SuccessInfo__NewInstall__Tests(unittest.TestCase):
    def _make_info(self):
        from ppic import SuccessInfo
        return SuccessInfo(
            _make_request("foo", previous_version=None),
            {
                "info": {"name": "foo", "version": "0.2"},
                "releases": {"0.2": [{"upload_time": "2014-12-04T23:16:25"}]}
            }
        )

    def test_update_candidates(self):
        info = self._make_info()
        result = self._callFUT([info])
        self.assertEqual(result["update_candidates"], [])

    def test_new_install_candidates(self):
        info = self._make_info()
        result = self._callFUT([info])
        self.assertEqual(result["new_install_candidates"], ["foo: '' -> '0.2'"])


@test_function("ppic:rendering_info_list")
class SuccessInfo__HasNotUpdate__Tests(unittest.TestCase):
    def _make_info(self):
        from ppic import SuccessInfo
        version = "0.2"
        return SuccessInfo(
            _make_request("foo", previous_version=version),
            {
                "info": {"name": "foo", "version": version},
                "releases": {version: [{"upload_time": "2014-12-04T23:16:25"}]}
            }
        )

    def test_update_candidates(self):
        info = self._make_info()
        result = self._callFUT([info])
        self.assertEqual(result["update_candidates"], [])

    def test_new_install_candidates(self):
        info = self._make_info()
        result = self._callFUT([info])
        self.assertEqual(result["new_install_candidates"], [])
