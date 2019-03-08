from __future__ import unicode_literals

import logging
import os
import pykka
import mopidy_yle
from mopidy.models import Image, Ref, Track, Album, SearchResult
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
        self.__config = config
        self.__backend = backend
        self.__yleapi = YLEAPI(config)
        
    def browse(self, uri):
        if not uri.startswith('yle:'):
            return []

        if uri == 'yle:root':
            return self.__yleapi.get_yle_categories()

        if uri.startswith('yle:category:'):
            item_url = uri.split(':')
            id = item_url[2]
            return self.__yleapi.get_yle_item(offset=0, category=id)

        if uri.startswith('yle:series:'):
            item_url = uri.split(':')
            id = item_url[2]
            return self.__yleapi.get_yle_item(offset=0, series=id)
        
        return []

    def search(self, query=None, uris=None, exact=False):
        for q in query:
            s = query[q][0]
            tracks = []
            albums = []
            data = self.__yleapi.get_yle_item(offset=0, query=s)
            for item in data:
                if item.type == 'track':
                    tracks.append(Track(name=item.name, uri=item.uri))
                elif item.type == 'album':
                    albums.append(Album(name=item.name, uri=item.uri))

        return SearchResult(tracks=tracks, albums=albums, uri=s)
    
    def get_images(self, uris):
        result = {}
        for uri in uris:
            uri_images = None
            if uri.startswith('yle:track:'):
                item_url = uri.split(':')
                program_id = item_url[2]
                image_url = self.__yleapi.get_yle_track_image_url(program_id)
                if image_url:
                    uri_images = [Image(uri=image_url)]
            if uri.startswith('yle:series:'):
                item_url = uri.split(':')
                id = item_url[2]
                image_url = self.__yleapi.get_yle_album_image_url(program_id)
                if image_url:
                    uri_images = [Image(uri=image_url)]
            result[uri] = uri_images or ()
        return result

    def lookup(self, uri):
        result = []
        if uri.startswith('yle:track:'):
            item_url = uri.split(':')
            program_id = item_url[2]
            result.append(self.__yleapi.get_yle_track_info(program_id, uri))
        if uri.startswith('yle:series:'):
            item_url = uri.split(':')
            program_id = item_url[2]
            result = self.__yleapi.get_yle_series_info(program_id, uri)
        return result
