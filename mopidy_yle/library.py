from __future__ import unicode_literals

import logging
import os
import pykka
import mopidy_yle
from mopidy.models import Image
from mopidy.models import Ref
from dateutil.parser import parse as parse_date
from mopidy import httpclient
from mopidy import backend
from mopidy import models

from .yleapi import YLEAPI

logger = logging.getLogger(__name__)


class YLELibraryProvider(backend.LibraryProvider):
    root_directory = Ref.directory(uri='yle:root', name='YLE')

    def __init__(self, config, backend):
        super(YLELibraryProvider, self).__init__(backend)
        logger.info('YLE init.')
        self.__config = config
        self.__backend = backend
        self.__yleapi = YLEAPI(config)
        
    def browse(self, uri):
        logger.warning('YLE browse() {0}'.format(uri))

        if not uri.startswith('yle:'):
            return []

        if uri == 'yle:root':
            return self.__yleapi.get_yle_categories()

        if uri.startswith('yle:category:'):
            item_url = uri.split(':')
            id = item_url[2]
            logger.warning('SUB')
            return self.__yleapi.get_yle_item(offset=0, category=id)

        if uri.startswith('yle:series:'):
            item_url = uri.split(':')
            id = item_url[2]
            logger.warning('SERIES: {0}'.format(id))
            return self.__yleapi.get_yle_item(offset=0, series=id)
        
        return []
    
    def get_images(self, uris):
        result = {}
        logger.warning('URIS: {0}'.format(uris))
        for uri in uris:
            uri_images = None
            if uri.startswith('yle:track:'):
                item_url = uri.split(':')
                program_id = item_url[2]
                uri_images = [Image(uri=self.__yleapi.get_yle_image_url(program_id))]
            result[uri] = uri_images or ()
        logger.info('IMAGES: {0}'.format(result))
        return result

    def lookup(self, uri):
        result = []
        logger.warning('LOOKUP: {0}'.format(uri))
        if uri.startswith('yle:track:'):
            item_url = uri.split(':')
            program_id = item_url[2]
            result.append(self.__yleapi.get_yle_track_info(program_id, uri))
        return result
