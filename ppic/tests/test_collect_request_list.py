# -*- coding:utf-8 -*-
import unittest
from evilunit import test_function
from unittest import mock


@test_function("ppic:collect_request_list")
class Tests(unittest.TestCase):
    def test_one__collect_all__is__False__one_found(self):
        class wana_install:
            foo = "foo"

        with mock.patch("ppic.RequestRepository", autospec=True) as m:
            m().find.return_value = wana_install.foo

            package_names = [wana_install.foo]
            result = self._callFUT(package_names, is_collect_all=False)

            self.assertEqual(result, [wana_install.foo])

    def test_one__collect_all__is__True__three_found(self):
        class wana_install:
            foo = "foo"

        class already_installed:
            bar = "bar"
            baz = "baz"

        with mock.patch("ppic.RequestRepository", autospec=True) as m:
            m().find.return_value = wana_install.foo
            m().collect_installed.return_value = [already_installed.bar, already_installed.baz]

            package_names = [wana_install.foo]
            result = self._callFUT(package_names, is_collect_all=True)

            expected = list(set([wana_install.foo,
                                 already_installed.bar,
                                 already_installed.baz]))
            self.assertEqual(list(set(result)), expected)

    def test_one__dupplicated_package_names(self):
        class wana_install:
            foo = "foo"

        with mock.patch("ppic.RequestRepository", autospec=True) as m:
            m().find.return_value = wana_install.foo

            package_names = [wana_install.foo, wana_install.foo, wana_install.foo]
            result = self._callFUT(package_names, is_collect_all=False)

            self.assertEqual(result, [wana_install.foo])

    def test_one__dupplicated_with_enrionment(self):
        class wana_install:
            foo = "foo"

        class already_install:
            foo = "foo"

        with mock.patch("ppic.RequestRepository", autospec=True) as m:
            m().find.return_value = wana_install.foo
            m().collect_installed.return_value = [already_install.foo]

            package_names = [wana_install.foo, wana_install.foo, wana_install.foo]
            result = self._callFUT(package_names, is_collect_all=True)

            self.assertEqual(result, [wana_install.foo])
