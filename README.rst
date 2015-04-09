ppic
========================================

ppic is python package information collector.

how to use
----------------------------------------

if your environment is such as below. ::

  $ pip freeze
  SQLAlchemy==0.9.7

``ppic`` command can collect information that need available updates are existed or not. ::

  $ ppic sqlalchemy ansible
  collection information .. takes at least 0.05 sec
  { 'packages': [ { 'name': 'SQLAlchemy',
                    '_previous_version': '0.9.7',
                    'version': '0.9.8',
                    'last_modified': '2014-10-13T17:16:15'},
                  { 'name': 'ansible',
                    'version': '1.8.2',
                    'last_modified': '2014-12-04T23:16:25'}],
    'update_candidates': ["SQLAlchemy: '0.9.7' -> '0.9.8'"], # update is found.
    'new_install_candidates': ["ansible: '' -> '1.8.2'"]}  # ansible is not found in your environment

``--installed`` option
----------------------------------------

``--installed`` (or ``-i``) option with ``ppic`` then collect all information in your in environment. ::


  $ ppic --installed
  collection information .. takes at least 0.00 sec
  { 'packages': [ { 'name': 'SQLAlchemy',
                    '_previous_version': '0.9.7',
                    'version': '0.9.8',
                    'last_modified': '2014-10-13T17:16:15'}],
    'update_candidates': ["SQLAlchemy: '0.9.7' -> '0.9.8'"], # update is found.
    'new_install_candidates': []}


``--stable-only`` option
----------------------------------------

``--stable-only`` (or ``-s``) option with ``ppic`` then collecting stable version only(but this is heuristic aproach maybe wrong, maybe)

::

  $ ppic django
  collecting information .. takes at least 0.0 sec
  {
    "packages": [
      {
        "name": "Django",
        "version": "1.8a1",
        "last_modified": "2015-01-16T22:25:13"
      }
    ],
    "update_candidates": [],
    "new_install_candidates": [
      "Django: '' -> '1.8a1'"
    ]
  }
  $ ppic django --stable-only
  collecting information .. takes at least 0.0 sec
  {
    "packages": [
      {
        "name": "Django",
        "version": "1.7.4",
        "last_modified": "2015-01-27T17:22:19"
      }
    ],
    "update_candidates": [],
    "new_install_candidates": [
      "Django: '' -> '1.7.4'"
    ]
  }

``--dependency`` option
----------------------------------------

``--dependency`` (or ``-d``) option with ``ppic`` then, collecting information in consideration of package dependency, so including dependents packages.

::

  {
    "packages": [
      {
        "name": "PasteDeploy", 
        "_previous_version": "1.5.2", 
        "version": "1.5.2", 
        "last_modified": "2013-12-27T17:41:02"
      }, 
      {
        "name": "WebOb", 
        "_previous_version": "1.4", 
        "version": "1.4", 
        "last_modified": "2014-05-15T01:30:57"
      }, 
      {
        "name": "pyramid", 
        "_previous_version": "1.5.1", 
        "version": "1.5.2", 
        "last_modified": "2014-11-10T05:06:15"
      }, 
      {
        "name": "repoze.lru", 
        "_previous_version": "0.6", 
        "version": "0.6", 
        "last_modified": "2012-07-12T20:48:40"
      }, 
      {
        "name": "setuptools", 
        "_previous_version": "3.6", 
        "version": "12.1", 
        "last_modified": "2015-02-11T01:16:43"
      }, 
      {
        "name": "translationstring", 
        "_previous_version": "1.1", 
        "version": "1.3", 
        "last_modified": "2014-11-05T20:19:35"
      }, 
      {
        "name": "venusian", 
        "_previous_version": "1.0", 
        "version": "1.0", 
        "last_modified": "2014-06-30T17:27:36"
      }, 
      {
        "name": "zope.deprecation", 
        "_previous_version": "4.1.1", 
        "version": "4.1.2", 
        "last_modified": "2015-01-13T15:28:52"
      }, 
      {
        "name": "zope.interface", 
        "_previous_version": "4.1.1", 
        "version": "4.1.2", 
        "last_modified": "2014-12-28T01:05:28"
      }
    ], 
    "update_candidates": [
      "pyramid: '1.5.1' -> '1.5.2'", 
      "setuptools: '3.6' -> '12.1'", 
      "translationstring: '1.1' -> '1.3'", 
      "zope.deprecation: '4.1.1' -> '4.1.2'", 
      "zope.interface: '4.1.1' -> '4.1.2'"
    ], 
    "new_install_candidates": [], 
    "dependencies": [
      {
        "pyramid": [
          "setuptools", 
          "WebOb", 
          "repoze.lru", 
          {
            "zope.interface": [
              "setuptools"
            ]
          }, 
          {
            "zope.deprecation": [
              "setuptools"
            ]
          }, 
          "venusian", 
          "translationstring", 
          "PasteDeploy"
        ]
      }, 
      {
        "zope.deprecation": [
          "setuptools"
        ]
      }, 
      {
        "zope.interface": [
          "setuptools"
        ]
      }
    ]
  }

appendix: using with ``jq``
----------------------------------------

::

  $ ppic pyramid --dependency| jq .update_candidates
  collecting information .. takes at least 0.4 sec 
  [
    "pyramid: '1.5.1' -> '1.5.2'",
    "setuptools: '3.6' -> '12.1'",
    "translationstring: '1.1' -> '1.3'",
    "zope.deprecation: '4.1.1' -> '4.1.2'",
    "zope.interface: '4.1.1' -> '4.1.2'"
  ]
