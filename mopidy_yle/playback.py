from __future__ import unicode_literals

import logging
import re

from mopidy import backend
from .yleapi import YLEAPI

import uritools

logger = logging.getLogger(__name__)


LIVERADIO = {
    'radio1': 'mms://winstr.yle.fi/liveyleradio1?MSWMExt=.asf',
    'puhe': 'mms://winstr.yle.fi/liveradiopuhe?MSWMExt=.asf',
    'suomi': 'mms://winstr.yle.fi/liveradiosuomi?MSWMExt=.asf'
}

class YLEPlaybackProvider(backend.PlaybackProvider):

    def __init__(self, config, audio, backend):
        super(YLEPlaybackProvider, self).__init__(audio, backend)
        self.__config = config
        self.__yleapi = YLEAPI(config)

    def translate_uri(self, uri):
        item_url = uri.split(':')
        program_id = item_url[2]
        if program_id in LIVERADIO:
            uri = LIVERADIO[program_id]
            return uri
        media_id = item_url[3]
        self.__yleapi.yle_report(program_id, media_id)
        return self.__yleapi.get_yle_media_url(program_id, media_id)

