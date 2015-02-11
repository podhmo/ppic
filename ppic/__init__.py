# -*- coding:utf-8 -*-
import re
import logging
logger = logging.getLogger(__name__)
import time
from .compat import urlopen_json, HTTPError
import argparse
import json
import sys
from collections import OrderedDict, namedtuple
try:
    from pip.utils import get_installed_distributions
except ImportError:
    from pip.util import get_installed_distributions
import pkg_resources


Request = namedtuple("Request", "name previous_version distribution")
Options = namedtuple("Options", "is_collect_all is_stable_only delay_time see_dependencies")

default_options = Options(is_collect_all=True,
                          is_stable_only=False,
                          see_dependencies=False,
                          delay_time=0.05)


class SuccessInfo(object):
    def __init__(self, request, info, options=default_options):
        self.request = request
        self.name = request.name
        self.info = info
        self.options = options

    @property
    def version(self):
        if not self.options.is_stable_only:
            return self.info["info"]["version"]

        version = self.info["info"]["stable_version"]
        if version is None:
            return self._guess_stable_version(sorted(self.info["releases"].keys(), reverse=True))
        return version

    unstable_rx = re.compile("[\._][0-9]*([_\-a-zA-Z]+[0-9]*)+$")

    def _guess_stable_version(self, version_candidates):
        # this is heuristic.
        # 1.8a, 1.8a1, 1.8x is unstable
        for v in version_candidates:
            if not self.unstable_rx.search(v):
                return v
        logger.info("allrelease is unstable: name=%s", self.name)
        return "xxx"

    @property
    def previous_version(self):
        return self.request.previous_version

    def _guess_last_modified(self, info, version):
        try:
            return info["releases"][version][0]["upload_time"]
        except IndexError:
            logger.info("releases not found: name=%s, version=%s", self.name, version)
            return ""

    def is_success(self):
        return True

    def is_new_install(self):
        return self.previous_version is None

    def has_update(self):
        return (not self.is_new_install()
                and self.previous_version != self.version)

    @property
    def project_name(self):
        try:
            return self.info["info"]["name"]  # project name
        except KeyError:
            return self.name

    def normalized_format(self):
        try:
            info = self.info
            r = OrderedDict()
            r["name"] = info["info"]["name"]
            if self.request.previous_version is not None:
                r["_previous_version"] = self.request.previous_version
            r["version"] = self.version
            r["last_modified"] = self._guess_last_modified(info, self.version)
            return r
        except (IndexError, KeyError):
            print(info["info"]["name"])
            raise


class FailureInfo(object):
    def __init__(self, request, msg, options=default_options):
        self.request = request
        self.name = request.name
        self.msg = msg
        self.options = options

    def normalized_format(self):
        r = OrderedDict()
        r["name"] = self.name
        r["error"] = self.msg
        return r

    def is_success(self):
        return False

    @property
    def project_name(self):
        return self.name


class RequestBuilder(object):
    def from_distribution(self, dist):
        # dict_keys(['location', 'py_version', '_provider', '_version', '_key', 'project_name', 'precedence', 'platform'])
        return Request(name=dist.project_name, previous_version=dist.version, distribution=dist)

    def dummy(self, name):
        return Request(name=name, previous_version=None, distribution=None)


class RequestRepository(object):
    def __init__(self, working_set=None):
        self.working_set = working_set or pkg_resources.working_set
        self._by_project_name = None
        self.builder = RequestBuilder()

    @property
    def by_project_name(self):
        if self._by_project_name is None:
            self._by_project_name = {d.project_name: d for d in self.by_key.values()}
        return self._by_project_name

    @property
    def by_key(self):
        return self.working_set.by_key

    def collect_installed(self):
        return [self.builder.from_distribution(d) for d in get_installed_distributions()]

    def _find_distribution(self, name):
        try:
            return self.by_key[name]
        except KeyError:
            return self.by_project_name.get(name)

    def find(self, name):
        d = self._find_distribution(name)
        if d is None:
            logger.info("distribution[name=%s] is not found", name)
            return self.builder.dummy(name)
        return self.builder.from_distribution(d)


def parse(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', action="store_true")  # deprecated
    parser.add_argument('--installed', action="store_true")
    parser.add_argument('--dependency', action="store_true")
    parser.add_argument('--stable-only', action="store_true")
    parser.add_argument("--delay", type=float, default=0.05)
    parser.add_argument('package', nargs="*")
    return parser.parse_args(args)


def get_info_from_request(request, options=default_options):
    url = "https://pypi.python.org/pypi/{name}/json".format(name=request.name)
    try:
        info = urlopen_json(url)
        return SuccessInfo(request, info, options)
    except HTTPError as e:
        return FailureInfo(request, str(e), options)


def collect_request_list(package_names, options):
    def recursive_collect(request):
        if request.distribution:
            for d in request.distribution.requires():
                request = repository.find(d.project_name)
                s.add(request)
                recursive_collect(request)

    s = set()
    repository = RequestRepository()
    if options.is_collect_all:
        s.update(repository.collect_installed())
    for name in package_names:
        request = repository.find(name)

        s.add(request)
        if options.see_dependencies:
            recursive_collect(request)
    return sorted(s, key=lambda r: r.name)


def collect_info_list(request_list, options=default_options):
    fmt = "collecting information .. takes at least {} sec \n"
    sys.stderr.write(fmt.format(options.delay_time * (len(request_list) - 1)))
    results = []
    for req in request_list:
        results.append(get_info_from_request(req, options))
        time.sleep(options.delay_time)  # delay for pypi server
    return results


def rendering_info_list(results):
    output_dict = OrderedDict(packages=[])
    output_dict["packages"] = [r.normalized_format() for r in results]

    output_dict["update_candidates"] = update_candidates = []
    output_dict["new_install_candidates"] = new_install_candidates = []

    for r in results:
        if not r.is_success():
            continue

        if r.is_new_install():
            new_install_candidates.append("{}: '' -> {!r}".format(r.project_name, r.version))
        elif r.has_update():
            update_candidates.append("{}: {!r} -> {!r}".format(r.project_name, r.previous_version, r.version))
    return output_dict


def main():
    parser = parse(sys.argv[1:])
    options = Options(
        is_collect_all=parser.all or parser.installed,
        is_stable_only=parser.stable_only,
        see_dependencies=parser.dependency,
        delay_time=parser.delay
    )
    request_list = collect_request_list(parser.package, options=options)
    results = collect_info_list(request_list, options=options)

    output_dict = rendering_info_list(results)
    print(json.dumps(output_dict, indent=2, ensure_ascii=False))
