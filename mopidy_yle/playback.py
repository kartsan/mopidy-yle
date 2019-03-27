from __future__ import unicode_literals

import logging

from mopidy import backend
from .yleapi import YLEAPI

logger = logging.getLogger(__name__)

class YLEPlaybackProvider(backend.PlaybackProvider):

    def __init__(self, config, audio, backend):
        super(YLEPlaybackProvider, self).__init__(audio, backend)
        self.__config = config
        self.__yleapi = YLEAPI(config)

    def translate_uri(self, uri):
        item_url = uri.split(':')
        media_type = item_url[1]
        program_id = item_url[2]
        if media_type == 'liveradio':
            uri = 'mms://winstr.yle.fi/{0}?MSWMExt=.asf'.format(program_id)
            return uri
        media_id = item_url[3]
        self.__yleapi.yle_report(program_id, media_id)
        return self.__yleapi.get_yle_media_url(program_id, media_id)

