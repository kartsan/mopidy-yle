from __future__ import unicode_literals

import logging
import os
import pykka
import mopidy_yle
from mopidy.models import Image, Ref, Track, Album, Artist, SearchResult
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
        result = []
        if not uri.startswith('yle:'):
            return result

        if uri == 'yle:root':
            categories = self.__yleapi.get_yle_category('root')
            for item in categories:
                result.append(Ref.directory(name=item['name'], uri=item['uri']))
            return result

        if uri.startswith('yle:category:'):
            item_url = uri.split(':')
            id = item_url[2]
            categories = self.__yleapi.get_yle_category(id)
            if categories:
                for item in categories:
                    result.append(Ref.directory(name=item['name'], uri=item['uri']))
            else:
                albums, tracks = self.__yleapi.get_yle_item(offset=0, category=id, limit=100)
                result = []
                for i in albums:
                    result.append(Ref.album(name=albums[i]['name'], uri=albums[i]['uri']))
            return result

        if uri.startswith('yle:series:'):
            item_url = uri.split(':')
            id = item_url[2]
            albums, tracks = self.__yleapi.get_yle_item(offset=0, series=id, limit=100)
            result = []
            for i in tracks:
                result.append(Ref.track(name=tracks[i]['name'], uri=tracks[i]['uri']))
#            for i in albums:
#                result.append(Ref.album(name=albums[i]['name'], uri=albums[i]['uri']))
            return result
        
        return result

    def search(self, query=None, uris=None, exact=False):
        tracklist = []
        albumlist = []
        artist = Artist(name='YLE Areena', uri='yle:artist:yleareena')
        for q in query:
            s = query[q][0]
            albums, tracks = self.__yleapi.get_yle_item(offset=0, query=s, limit=100)
            if q != 'album':
                for item in tracks:
                    if 'album' in tracks[item] and tracks[item]['album']:
                        album = Album(name=tracks[item]['album']['name'],
                                      uri=tracks[item]['album']['uri'],
                                      artists=[artist])
                        tracklist.append(Track(name=tracks[item]['name'], uri=tracks[item]['uri'], artists=[artist], album=album))
                    else:
                        tracklist.append(Track(name=tracks[item]['name'], uri=tracks[item]['uri'], artists=[artist]))
            for item in albums:
                image = albums[item]['image']
                if image:
                    albumlist.append(Album(name=albums[item]['name'], uri=albums[item]['uri'], images=[image], artists=[artist]))
                else:
                    albumlist.append(Album(name=albums[item]['name'], uri=albums[item]['uri'], artists=[artist]))
        return SearchResult(tracks=tracklist, albums=albumlist, uri='yle:search:{0}'.format(query))
    
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
#        if uri.startswith('yle:artist:'):
        if uri.startswith('yle:track:'):
            item_url = uri.split(':')
            program_id = item_url[2]
            track = self.__yleapi.get_yle_track_info(program_id, uri)
            if not track:
                return result
            artist = models.Artist(name=track['artist'], uri='yle:artist:yleareena') 
            result.append(models.Track(name=track['name'], uri=track['uri'], length=track['length'], artists=[artist], date='2008-12-26'))
        if uri.startswith('yle:series:'):
            item_url = uri.split(':')
            program_id = item_url[2]
            tracks = self.__yleapi.get_yle_series_info(program_id, uri)
            for track in tracks:
                artist = models.Artist(name=track['artist'], uri='yle:artist:yleareena')
                album = models.Album(name=track['album']['name'], uri=track['album']['uri'])
                result.append(models.Track(name=track['name'], uri=track['uri'], length=track['length'], artists=[artist], date='2008-12-26', album=album))
        return result
