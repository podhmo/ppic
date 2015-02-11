# -*- coding:utf-8 -*-
import unittest
from evilunit import test_function
from unittest import mock


@test_function("ppic:collect_request_list")
class Tests(unittest.TestCase):
    def _callFUT(self, package_name, is_collect_all):
        from ppic import Options
        options = Options(
            is_collect_all=is_collect_all,
            is_stable_only=False,
            see_dependencies=False,
            delay_time=0,
            cache_path=None,
            cache_timeout=0
        )
        return self._getTarget()(package_name, options)

    def test_one__collect_all__is__False__one_found(self):
        class wana_install:
            class foo:
                name = "foo"

        with mock.patch("ppic.RequestRepository", autospec=True) as m:
            m().find.return_value = wana_install.foo

            package_names = [wana_install.foo]
            result = self._callFUT(package_names, is_collect_all=False)

            self.assertEqual(result, [wana_install.foo])

    def test_one__collect_all__is__True__three_found(self):
        class wana_install:
            class foo:
                name = "foo"

        class already_installed:
            class bar:
                name = "bar"

            class baz:
                name = "baz"

        with mock.patch("ppic.RequestRepository", autospec=True) as m:
            m().find.return_value = wana_install.foo
            m().collect_installed.return_value = [already_installed.bar, already_installed.baz]

            package_names = [wana_install.foo]
            result = self._callFUT(package_names, is_collect_all=True)

            expected = [already_installed.bar, already_installed.baz, wana_install.foo]
            self.assertEqual(result, expected)

    def test_one__dupplicated_package_names(self):
        class wana_install:
            class foo:
                name = "foo"

        with mock.patch("ppic.RequestRepository", autospec=True) as m:
            m().find.return_value = wana_install.foo

            package_names = [wana_install.foo, wana_install.foo, wana_install.foo]
            result = self._callFUT(package_names, is_collect_all=False)

            self.assertEqual(result, [wana_install.foo])

    def test_one__dupplicated_with_enrionment(self):

        class wana_install:
            class foo:
                name = "foo"

        class already_install:
            foo = wana_install.foo

        with mock.patch("ppic.RequestRepository", autospec=True) as m:
            m().find.return_value = wana_install.foo
            m().collect_installed.return_value = [already_install.foo]

            package_names = [wana_install.foo, wana_install.foo, wana_install.foo]
            result = self._callFUT(package_names, is_collect_all=True)

            self.assertEqual(result, [wana_install.foo])
