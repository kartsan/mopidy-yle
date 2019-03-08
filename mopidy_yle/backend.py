from __future__ import unicode_literals

import logging
import os
import pykka
from mopidy import backend

from .library import YLELibraryProvider
from .playback import YLEPlaybackProvider
from .yleapi import YLEAPI

logger = logging.getLogger(__name__)


class YLEBackend(pykka.ThreadingActor, backend.Backend):
    uri_schemes = [ 'yle' ]
    
    def __init__(self, config, audio):
        super(YLEBackend, self).__init__()
        self.library = YLELibraryProvider(config, backend=self)
        self.playback = YLEPlaybackProvider(config, audio, backend=self)
