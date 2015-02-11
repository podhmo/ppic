# -*- coding:utf-8 -*-
import logging
logger = logging.getLogger(__name__)
import time
import urllib.request
from urllib.error import HTTPError
import pprint
import argparse
import json
import sys
from collections import OrderedDict, namedtuple
from pip.util import get_installed_distributions
import pkg_resources


Request = namedtuple("Request", "name previous_version")


class SuccessInfo(object):
    def __init__(self, request, info):
        self.request = request
        self.name = request.name
        self.info = info

    def guess_last_modified(self, info, version):
        try:
            return info["releases"][version][0]["upload_time"]
        except IndexError:
            logger.info("releases not found: name=%s, version=%s", self.name, version)
            return ""

    def normalized_format(self):
        try:
            info = self.info
            version = info["info"]["version"]
            r = OrderedDict()
            r["name"] = info["info"]["name"]
            if self.request.previous_version is not None:
                r["_previous_version"] = self.request.previous_version
            r["version"] = version
            r["last_modified"] = self.guess_last_modified(info, version)
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


class RequestBuilder(object):
    def from_distribution(self, dist):
        # dict_keys(['location', 'py_version', '_provider', '_version', '_key', 'project_name', 'precedence', 'platform'])
        return Request(name=dist.project_name, previous_version=dist.version)

    def dummy(self, name):
        return Request(name=name, previous_version=None)


class RequestRepository(object):
    def __init__(self, working_set=None):
        self.working_set = working_set or pkg_resources.working_set
        self.builder = RequestBuilder()

    def collect_installed(self):
        return [self.builder.from_distribution(d) for d in get_installed_distributions()]

    def find(self, name):
        try:
            return self.builder.from_distribution(self.working_set.by_key[name])
        except KeyError:
            logger.info("distribution[name=%s] is not found", name)
            return self.builder.dummy(name)


def parse(args):
    parser = argparse.ArgumentParser()
    parser.add_argument('--all', action="store_true")
    parser.add_argument("--delay", type=float)
    parser.add_argument('package', nargs="*")
    return parser.parse_args(args)


def get_info_from_package_name(request):
    url = "https://pypi.python.org/pypi/{name}/json".format(name=request.name)
    try:
        info = json.loads(urllib.request.urlopen(url).readall().decode("utf-8"))
        return SuccessInfo(request, info)
    except HTTPError as e:
        return FailureInfo(request, str(e))


DELAY_TIME = 0.05


def main():
    parser = parse(sys.argv[1:])
    repository = RequestRepository()
    if parser.all:
        request_list = repository.collect_installed()
    else:
        request_list = [repository.find(p) for p in parser.package]

    delay_time = parser.delay or DELAY_TIME

    r = OrderedDict(packages=[])
    sys.stderr.write("collection information .. takes at least {} sec \n".format(delay_time * (len(request_list) - 1)))
    for request in request_list:
        r["packages"].append((get_info_from_package_name(request)).normalized_format())
        time.sleep(delay_time)  # delay for pypi server

    r["update_candidates"] = update_candidates = []
    r["new_install_candidates"] = new_install_candidates = []
    for p in r["packages"]:
        version = p["version"]
        previous_version = p.get("_previous_version")
        if previous_version is None:
            new_install_candidates.append("{}: '' -> {!r}".format(p["name"], version))
            continue
        if version == previous_version:
            continue
        update_candidates.append("{}: {!r} -> {!r}".format(p["name"], previous_version, version))
    pprint.pprint(r, indent=2)
