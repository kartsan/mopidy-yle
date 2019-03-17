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

LIVERADIO = {
    'liveyleradio1': 'YLE Radio 1',
    'liveradiopuhe': 'YLE Puhe',
    'liveradiosuomi': 'YLE Radio Suomi',
    'a_radiohame': u'YLE H\xe4me',
    'a_keskisuomi': u'YLE Jyv\xe4skyl\xe4',
    'a_kainuu': 'YLE Kajaani',
    'a_perameri': 'YLE Kemi',
    'a_keskipohjanmaa': 'YLE Kokkola',
    'a_kymenlaakso': 'YLE Kotka',
    'a_radiosavo': 'YLE Kuopio',
    'a_lahdenradio': 'YLE Lahti',
    'a_etelakarjala': 'YLE Lappeenranta',
    'a_etelasavo': 'YLE Mikkeli',
    'a_ouluradio': 'YLE Oulu',
    'a_pohjanmaa': 'YLE Pohjanmaa',
    'a_satakunta': 'YLE Pori',
    'a_lapinradio': 'YLE Rovaniemi',
    'a_tampere': 'YLE Tampere',
    'a_turunradio' : 'YLE Turku'
}

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
            result.append(Ref.directory(name='Live radio', uri='yle:category:live'))
            return result

        elif uri.startswith('yle:category:'):
            item_url = uri.split(':')
            id = item_url[2]
            result = []
            if id == 'live':
                for station in LIVERADIO:
                    result.append(Ref.track(name=LIVERADIO[station], uri='yle:liveradio:{0}'.format(station)))
            else:
                categories = self.__yleapi.get_yle_category(id)
                if categories:
                    for item in categories:
                        result.append(Ref.directory(name=item['name'], uri=item['uri']))
                else:
                    albums, tracks = self.__yleapi.get_yle_item(offset=0, category=id, limit=100)
                    for i in albums:
                        result.append(Ref.album(name=albums[i]['name'], uri=albums[i]['uri']))
            return result

        elif uri.startswith('yle:series:'):
            item_url = uri.split(':')
            id = item_url[2]
            tracks = self.__yleapi.get_yle_series_info(id)
            result = []
            for track in tracks:
                result.append(Ref.track(name=track['name'], uri=track['uri']))
            return result

        return result

    def search(self, query=None, uris=None, exact=False):
        tracklist = []
        albumlist = []
        for q in query:
            s = query[q][0]
            albums, tracks = self.__yleapi.get_yle_item(offset=0, query=s, limit=100)
            if q != 'album':
                for item in tracks:
                    album = Album()
                    if tracks[item]['album']:
                        album_item = albums[tracks[item]['album']]
                        album = Album(name=album_item['name'],
                                      uri=album_item['uri'])
                    tracklist.append(Track(name=tracks[item]['name'], uri=tracks[item]['uri'], album=album, comment=tracks[item]['comment']))
            for item in albums:
                image = Image()
                if albums[item]['image']:
                    image = albums[item]['image']
                    albumlist.append(Album(name=albums[item]['name'], uri=albums[item]['uri'], images=[image]))
                else:
                    albumlist.append(Album(name=albums[item]['name'], uri=albums[item]['uri']))
        return SearchResult(tracks=tracklist, albums=albumlist, uri='yle:search:{0}'.format(query))
    
    def get_images(self, uris):
        result = {}
        for uri in uris:
            uri_images = None
            if uri.startswith('yle:track:'):
                item_url = uri.split(':')
                program_id = item_url[2]
                image_url = self.__yleapi.get_yle_image_url(program_id)
                if image_url:
                    uri_images = [Image(uri=image_url)]
            elif uri.startswith('yle:series:'):
                item_url = uri.split(':')
                id = item_url[2]
                image_url = self.__yleapi.get_yle_image_url(program_id)
                if image_url:
                    uri_images = [Image(uri=image_url)]
            elif uri.startswith('yle:liveradio:'):
                image_url = self.__yleapi.get_yle_logo()
                if image_url:
                    uri_images = [Image(uri=image_url)]
            result[uri] = uri_images or ()
        return result

    def lookup(self, uri):
        result = []
        if uri.startswith('yle:liveradio'):
            item_url = uri.split(':')
            program_id = item_url[2]
            album = Album(name='YLE live',
                          uri=uri,
                          images=[self.__yleapi.get_yle_logo()])
            result.append(models.Track(name=LIVERADIO[program_id], uri=uri, album=album))
        elif uri.startswith('yle:track:'):
            item_url = uri.split(':')
            program_id = item_url[2]
            track = self.__yleapi.get_yle_track(program_id)
            if not track:
                return result
            album = Album()
            if track['album']:
                album = self.__yleapi.get_yle_album(track['album'])
                if album:
                    album = Album(name=album['name'],
                                  uri=album['uri'],
                                  images=[album['image']])
            result.append(models.Track(name=track['name'],
                                       uri=track['uri'],
                                       length=track['length'],
                                       album=album,
                                       comment=track['comment']))
        elif uri.startswith('yle:series:'):
            item_url = uri.split(':')
            program_id = item_url[2]
            tracks = self.__yleapi.get_yle_series_info(program_id)
            for track in tracks:
                album = Album()
                if track['album']:
                    album = self.__yleapi.get_yle_album(track['album'])
                    if album:
                        album = Album(name=album['name'],
                                      uri=album['uri'],
                                      images=[album['image']])
                result.append(models.Track(name=track['name'],
                                           uri=track['uri'],
                                           length=track['length'],
                                           album=album,
                                           comment=track['comment']))
        return result
