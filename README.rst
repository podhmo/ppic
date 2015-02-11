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

``--all`` option
----------------------------------------

``--all`` option with ``ppic`` then collect all information in your in environment. ::


  $ ppic --all
  collection information .. takes at least 0.00 sec
  { 'packages': [ { 'name': 'SQLAlchemy',
                    '_previous_version': '0.9.7',
                    'version': '0.9.8',
                    'last_modified': '2014-10-13T17:16:15'}],
    'update_candidates': ["SQLAlchemy: '0.9.7' -> '0.9.8'"], # update is found.
    'new_install_candidates': []}


``--stable-only`` option
----------------------------------------

``--stable-only`` option with ``ppic`` then collecting stable version only(but this is heuristic aproach maybe wrong, maybe)

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

