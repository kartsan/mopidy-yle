from __future__ import unicode_literals

import logging
import os

from mopidy import config, ext
from mopidy import httpclient

__version__ = '0.3.0'

SORT_FIELDS = ['%s:%s' % (f, o) for o in ('asc', 'desc') for f in (
    'playcount.6h',
    'playcount.24h',
    'playcount.week',
    'playcount.month',
    'publication.starttime',
    'publication.endtime',
    'updated'
)]

logger = logging.getLogger(__name__)


class Extension(ext.Extension):

    dist_name = 'Mopidy-YLE'
    ext_name = 'yle'
    version = __version__

    def get_default_config(self):
        conf_file = os.path.join(os.path.dirname(__file__), 'ext.conf')
        return config.read(conf_file)

    def get_config_schema(self):
        schema = super(Extension, self).get_config_schema()
        # TODO: Add missing and do error checking
        schema['app_id'] = config.String()
        schema['app_key'] = config.String()
        schema['secret_key'] = config.String(optional=True)
        schema['sort_method'] = config.String(choices=SORT_FIELDS, optional=True)
        schema['language'] = config.String(optional=True)
        
        return schema

    def setup(self, registry):
        from .backend import YLEBackend
        registry.add('backend', YLEBackend)
