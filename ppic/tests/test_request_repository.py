# -*- coding:utf-8 -*-
import unittest
from evilunit import test_target


@test_target("ppic:RequestRepository")
class FindTests(unittest.TestCase):
    def test_not_found__previous_version_isNone(self):
        target = self._makeOne()
        result = target.find("this-is-not-found-package-name")
        self.assertEqual(result.name, "this-is-not-found-package-name")
        self.assertEqual(result.previous_version, None)

    def test_found__by_key__previous_version_is_not_None(self):
        target = self._makeOne()
        # pip is exists, absolutely.
        import pkg_resources
        assert pkg_resources.working_set.by_key["pip"]

        result = target.find("pip")
        self.assertEqual(result.name, "pip")
        self.assertIsNotNone(result.previous_version)

    def test_found__by_project_name__previous_version_is_not_None(self):
        class mockin_pip:
            project_name = "python-pip"
            version = "0.1"

        class WorkingSet:
            by_key = {"pip": mockin_pip}

        target = self._makeOne(WorkingSet())
        result = target.find("python-pip")
        self.assertEqual(result.name, "python-pip")  # name is project name
        self.assertEqual(result.previous_version, mockin_pip.version)  # important


@test_target("ppic:RequestRepository")
class CollectInstalledPackagesTests(unittest.TestCase):
    def test_it(self):
        target = self._makeOne()
        result = target.collect_installed()
        self.assertTrue(len(result) >= 1)
        self.assertIsNotNone(result[0].previous_version)
