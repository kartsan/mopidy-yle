****************************
Mopidy-YLE
****************************

.. image:: https://img.shields.io/pypi/v/Mopidy-YLE.svg?style=flat
    :target: https://pypi.python.org/pypi/Mopidy-YLE/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/travis/kartsan/mopidy-yle/master.svg?style=flat
    :target: https://travis-ci.org/kartsan/mopidy-yle
    :alt: Travis CI build status

.. image:: https://img.shields.io/coveralls/kartsan/mopidy-yle/master.svg?style=flat
   :target: https://coveralls.io/r/kartsan/mopidy-yle
   :alt: Test coverage

Mopidy extension for YLE Areena


Installation
============

Install by running::

    git clone https://github.com/kartsan/mopidy-yle.git
    sudo python setup.py install


Configuration
=============

Before starting Mopidy, you must add configuration for
Mopidy-YLE to your Mopidy configuration file::

    [yle]
    app_id = <your YLE app_id>
    app_key = <your YLE app_key>
    secret_key = <your YLE secret_key>
    sort_method = publication.starttime
    sort_type = asc
    language = fi

The following configuration values are available:

- ``yle/enabled``: If the YLE extension should be ``true`` (enabled) or ``false`` (not). Defaults to ``true``.

- ``yle/app_id``: Your personal YLE application ID. Required.

- ``yle/app_key``: Your personal YLE application key. Required.

- ``yle/secret_key``: Your personal YLE secret key. It is used to decode media URIs. Required if any media is about to be played.

- ``yle/sort_method``: Sorting method to use in searches. Available methods are: ``playcount.6h``, ``playcount.24h``, ``playcount.week``, ``playcount.month``, ``publication.starttime``, ``publication.endtime`` and ``updated``. Defaults to ``publication.starttime``.

- ``yle/sort_type``: Sorting type to use in searches. Available types are: ``asc`` (ascending order), ``desc`` (descending order). Defaults to ``asc``.

- ``yle/language``: Accepted language in the search results. Available languages are: ``fi`` (Finnish), ``sv`` (Swedish) and ``en`` (English). Defaults to ``fi``.

Get your API personal keys from `here <https://tunnus.yle.fi/api-avaimet>`_


Project resources
=================

- `Source code <https://github.com/kartsan/mopidy-yle>`_
- `Issue tracker <https://github.com/kartsan/mopidy-yle/issues>`_


Credits
=======

- Original author: `Ilkka Karvinen <https://github.com/kartsan`__
- Current maintainer: `Ilkka Karvinen <https://github.com/kartsan`__
- `Contributors <https://github.com/kartsan/mopidy-yle/graphs/contributors>`_


Changelog
=========

v0.2.0 (Initial release)
----------------------------------------

- First public release: search, browse and playing media works.


v0.1.0 (UNRELEASED)
----------------------------------------

- Initial release.
