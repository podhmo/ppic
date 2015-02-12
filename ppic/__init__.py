# -*- coding:utf-8 -*-
import re
import logging
logger = logging.getLogger(__name__)
import os.path
import argparse
import json
import sys
from collections import OrderedDict, namedtuple
try:
    from pip.utils import get_installed_distributions
except ImportError:
    from pip.util import get_installed_distributions
import pkg_resources
import tempfile
from distlib.version import NormalizedVersion, UnsupportedVersionError
from .resource import PYPIJSONResource, CachedResourceWrapper


Request = namedtuple("Request", "name previous_version distribution")
Options = namedtuple("Options", "is_collect_all is_stable_only delay_time see_dependencies cache_path cache_timeout")

default_options = Options(is_collect_all=True,
                          is_stable_only=False,
                          see_dependencies=False,
                          cache_path=os.path.join(tempfile.gettempdir(), "ppic.json"),
                          cache_timeout=60 * 10,
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
            # todo:test
            versions = sorted(self.info["releases"].keys(), reverse=True, key=self.maybe_version)
            return self._guess_stable_version(versions)
        return version

    def maybe_version(self, v):
        try:
            return NormalizedVersion(v)
        except UnsupportedVersionError:
            return NormalizedVersion("0")

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
        except (IndexError, KeyError):
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
    parser.add_argument('--all', action="store_true", help="(deprecated) same as --installed")  # deprecated
    parser.add_argument('--installed', action="store_true", help="collecting installed packages information in your env")
    parser.add_argument('--dependency', action="store_true", help="collecting dependents package's information")
    parser.add_argument('--stable-only', action="store_true", help="newest stable version(guessing)")
    parser.add_argument('--no-cache', action="store_true", help="doesn't using temporary cache(timeout default is 10min)")
    parser.add_argument('--cache-timeout', default=default_options.cache_timeout, type=int, help="temporary cache timeout(seconds)")
    parser.add_argument('--logging', choices=["debug", "info"], default=None, help="activation for logging message")
    parser.add_argument("--delay", type=float, default=0.05, help="delay time of each request")
    parser.add_argument('package', nargs="*")
    return parser.parse_args(args)


def get_info_from_request(resource, request, options=default_options):
    info_or_error, status = resource.access(request)
    if status:
        return SuccessInfo(request, info_or_error, options)
    else:
        return FailureInfo(request, info_or_error, options)


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


def collect_info_list(request_list, options=default_options, usecache=False):
    fmt = "collecting information .. takes at least {} sec \n"
    sys.stderr.write(fmt.format(options.delay_time * (len(request_list) - 1)))
    results = []
    resource = PYPIJSONResource(options.delay_time)
    if usecache:
        resource = CachedResourceWrapper(resource, options.cache_path, options.cache_timeout)
    with resource.using():
        for req in request_list:
            results.append(get_info_from_request(resource, req, options))
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


def collect_dependencies(request, history, working_set=pkg_resources.working_set):
    if request.distribution is None:
        return {request.name: "UNKNOWN"}

    def rec(dist, initial):
        if dist is None:
            return None
        if dist._key in history:
            children = history[dist._key]
            if initial and len(children) <= 0:
                return None
            return {dist.project_name: children} if len(children) > 0 else dist.project_name

        children = history[dist._key] = []
        for r in dist.requires():
            child = rec(working_set.by_key.get(r.key), initial=False)
            if child is not None:
                children.append(child)
        if initial and len(children) <= 0:
            return None
        return {dist.project_name: children} if len(children) > 0 else dist.project_name
    return rec(request.distribution, initial=True)


def main():
    parser = parse(sys.argv[1:])
    if parser.logging:
        logger.setLevel(getattr(logging, parser.logging.upper()))
        logger.addHandler(logging.StreamHandler())

    options = Options(
        is_collect_all=parser.all or parser.installed,
        is_stable_only=parser.stable_only,
        see_dependencies=parser.dependency,
        delay_time=parser.delay,
        cache_path=default_options.cache_path,
        cache_timeout=parser.cache_timeout
    )
    request_list = collect_request_list(parser.package, options=options)
    results = collect_info_list(request_list, options=options, usecache=not parser.no_cache)

    output_dict = rendering_info_list(results)
    if options.see_dependencies:
        history = {}
        maybe_dependencies = [collect_dependencies(req, history=history) for req in request_list]
        output_dict["dependencies"] = [e for e in maybe_dependencies if e is not None]
    print(json.dumps(output_dict, indent=2, ensure_ascii=False))
