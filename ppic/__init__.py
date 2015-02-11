# -*- coding:utf-8 -*-
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


Request = namedtuple("Request", "name previous_version")


class SuccessInfo(object):
    def __init__(self, request, info):
        self.request = request
        self.name = request.name
        self.info = info

    @property
    def version(self):
        return self.info["info"]["version"]

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
    def __init__(self, request, msg):
        self.request = request
        self.name = request.name
        self.msg = msg

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
        return Request(name=dist.project_name, previous_version=dist.version)

    def dummy(self, name):
        return Request(name=name, previous_version=None)


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
    parser.add_argument('--all', action="store_true")
    parser.add_argument("--delay", type=float)
    parser.add_argument('package', nargs="*")
    return parser.parse_args(args)


def get_info_from_request(request):
    url = "https://pypi.python.org/pypi/{name}/json".format(name=request.name)
    try:
        info = urlopen_json(url)
        return SuccessInfo(request, info)
    except HTTPError as e:
        return FailureInfo(request, str(e))


DELAY_TIME = 0.05


def collect_request_list(package_names, is_collect_all=False):
    s = set()
    repository = RequestRepository()
    if is_collect_all:
        s.update(repository.collect_installed())
    for name in package_names:
        s.add(repository.find(name))
    return sorted(s, key=lambda r: r.name)


def main():
    parser = parse(sys.argv[1:])
    request_list = collect_request_list(parser.package, parser.all)
    delay_time = parser.delay or DELAY_TIME
    results = collect_info_list(request_list, delay_time=delay_time)

    output_dict = rendering_info_list(results)
    print(json.dumps(output_dict, indent=2, ensure_ascii=False))


def collect_info_list(request_list, delay_time=DELAY_TIME):
    fmt = "collection information .. takes at least {} sec \n"
    sys.stderr.write(fmt.format(delay_time * (len(request_list) - 1)))
    results = []
    for req in request_list:
        results.append(get_info_from_request(req))
        time.sleep(delay_time)  # delay for pypi server
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
