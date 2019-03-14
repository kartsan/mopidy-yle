from __future__ import unicode_literals
import logging
import os
import pykka
import base64
import requests
import isodate
from mopidy import httpclient
from Crypto.Cipher import AES
from . import Extension

logger = logging.getLogger(__name__)

class YLEAPI:
    yle_url = 'https://external.api.yle.fi/v1'
    yle_image_url = 'http://images.cdn.yle.fi/image/upload/w_320,h_320,c_fit'
    yle_report_url = 'https://external.api.yle.fi/v1/tracking/streamstart'
    unplayableCategories = ['5-162', '5-164', '5-226', '5-228']
    radioCategory = '5-200'
    __categories = []
    __tracks = {}
    __albums = {}
    
    def __init__(self, config):
        self.__config = config
        self.__dist_name = Extension.dist_name
        self.__version = Extension.version
        
    def get_yle_json(self, url):
        session = self.get_requests_session()
        try:
            response = session.get(url).json()
            return response
        except:
            # TODO: Have some more detailed exception handling
            print('Error getting url {0}'.format(url))
            pass
        return None

    def get_yle_series(self, id):
        return self.get_yle_json('{0}/series/items/{1}.json?app_id={2}&app_key={3}'.format(self.yle_url, id, self.__config['yle']['app_id'], self.__config['yle']['app_key']))

    def get_yle_program(self, id):
        return self.get_yle_json('{0}/programs/items/{1}.json?app_id={2}&app_key={3}'.format(self.yle_url, id, self.__config['yle']['app_id'], self.__config['yle']['app_key']))

    def get_yle_categories(self):
        if not YLEAPI.__categories:
            data = self.get_yle_json('{0}/programs/categories.json?key=radio&app_id={1}&app_key={2}'.format(self.yle_url, self.__config['yle']['app_id'], self.__config['yle']['app_key']))
            YLEAPI.__categories = self.parse_yle_categories(data['data'])

    def get_yle_category(self, id):
        result = []
        self.get_yle_categories()
        if id == 'root':
            for item in YLEAPI.__categories:
                if 'broader' not in item:
                    if item['key'] == 'radio':
                        id = item['id']
                        break
        if not id:
            return result
        for item in YLEAPI.__categories:
            if 'broader' in item:
                if item['broader']['id'] == id:
                    result.append(item)
        return result

    # TODO: Move this out of API source
    def get_requests_session(self):
        proxy = httpclient.format_proxy(self.__config['proxy'])
        full_user_agent = httpclient.format_user_agent('%s/%s' % (self.__dist_name, self.__version))
        
        session = requests.Session()
        session.proxies.update({'http': proxy, 'https': proxy})
        session.headers.update({'user-agent': full_user_agent})
        
        return session

    def get_yle_item(self, offset, query=None, category=None, limit=None, series=None):
        parameters = ['availability=ondemand', 'mediaobject=audio', 'type=radiocontent']
        if category:
            parameters.append('category={0}'.format(category))
        if query:
            parameters.append('q={0}'.format(query))
        if limit:
            parameters.append('limit={0}'.format(limit))
        if series:
            parameters.append('series=' + series)
        parameters.append('order=' + self.get_yle_sort_method())
        parameters.append('offset=' + str(offset))
        parameters.append('app_id=' + self.__config['yle']['app_id'])
        parameters.append('app_key=' + self.__config['yle']['app_key'])
        parameters.append('contentprotection=22-0,22-1')
        items = self.get_yle_json('{0}/programs/items.json?{1}'.format(self.yle_url, '&'.join(parameters)))
        return self.parse_items(items['data'])

    def parse_yle_categories(self, categories):
        result = []
        for item in categories:
            id = item['id']
            title = item['title'][self.__config['yle']['language']]
            if 'broader' not in item:
                result.append({'name': title,
                               'id': id,
                               'uri': 'yle:category:{0}'.format(id),
                               'key': item['key']})
            else:
                result.append({'name': title,
                               'id': id,
                               'uri': 'yle:category:{0}'.format(id),
                               'broader': item['broader'],
                               'key': item['key']})
        return result

    def fill_album(self, item):
        id = item['partOfSeries']['id']
        if id in YLEAPI.__albums:
            return id
        image = None
        try:
            title = item['partOfSeries']['title'][self.__config['yle']['language']]
        except KeyError:
            # Not for this language
            return None
        if 'coverImage' in item['partOfSeries']:
            image = self.get_yle_image_url(item['partOfSeries']['coverImage']['id'])
        YLEAPI.__albums[id] = { 'type': 'album',
                                'id': id,
                                'name': title,
                                'uri': 'yle:series:{0}'.format(id),
                                'image' : image,
                                'tracks' : [],
                                'artist' : 'YLE Areena' }
        return id

    def parse_items(self, items):
        result = []
        album_id = None
        albums = {}
        tracks = {}
        albumcount = 0
        trackcount = 0
        for item in items:
            id = item['id']
            if 'publicationEvent' in item:
                try:
                    title = item['title'][self.__config['yle']['language']]
                except KeyError:
                    # Not for this language
                    continue
                if 'partOfSeries' in item:
                    album_id = self.fill_album(item)
                    if album_id:
                        albums[album_id] = YLEAPI.__albums[album_id]
                for event in item['publicationEvent']:
                    if event['temporalStatus'] == 'currently' and event['type'] == 'OnDemandPublication':
                        media_id = event['media']['id']
                        duration = event['media']['duration']
                        if not event['media']['type'] == 'AudioObject':
                            logger.warning('No audio available in the program')
                            continue
                        item['length'] = length = 1000 * isodate.parse_duration(duration).seconds
                        tracks[id] = { 'type': 'track', 'name': title,
                                       'id': id,
                                       'uri': 'yle:track:{0}:{1}'.format(id, media_id),
                                       'album': album_id,
                                       'length': length,
                                       'artist' : 'YLE Areena' }
                        YLEAPI.__tracks[id] = tracks[id]
        return albums, tracks

    def get_yle_sort_method(self):
        sort_type = self.__config['yle']['sort_type']
        sort_method = self.__config['yle']['sort_method']
        
        if not sort_type in ['asc', 'desc']:
            raise ValueError('Unknown sort type {0}'.format(sort_type))
        
        if not sort_method in [ 'playcount.6h', 'playcount.24h', 'playcount.week', 'playcount.month', 'publication.starttime', 'publication.endtime', 'updated' ]:
            raise ValueError('Unknown sort method {0}'.format(sort_method))

        return '{0}:{1}'.format(sort_method, sort_type)

    def get_yle_media_url(self, program_id, media_id):
        encrypted_data = self.get_yle_json('{0}/media/playouts.json?program_id={1}&media_id={2}&protocol=PMD&app_id={3}&app_key={4}'.format(self.yle_url, program_id, media_id, self.__config['yle']['app_id'], self.__config['yle']['app_key']))
        if not encrypted_data:
            return None
        encrypted_url = encrypted_data['data'][0]['url']
        enc = base64.b64decode(encrypted_url)
        iv = enc[:16]
        cipher = AES.new(self.__config['yle']['secret_key'], AES.MODE_CBC, iv)
        decrypted_url = cipher.decrypt(enc[16:])
        url = decrypted_url[:-ord(decrypted_url[len(decrypted_url)-1:])]
        return url

    def yle_report(self, program_id, media_id):
        self.get_yle_json('{0}?program_id={1}&media_id={2}&app_id={3}&app_key={4}'.format(self.yle_report_url, program_id, media_id, self.__config['yle']['app_id'], self.__config['yle']['app_key']))

    def get_yle_track_info(self, program_id):
        if YLEAPI.__tracks:
            if program_id in YLEAPI.__tracks:
                return YLEAPI.__tracks[program_id]

        return {}

    def get_yle_track(self, track_id):
        return YLEAPI.__tracks[track_id]

    def get_yle_album(self, album_id):
        return YLEAPI.__albums[album_id]

    def get_yle_series_info(self, series_id):
        if series_id in YLEAPI.__albums:
            if YLEAPI.__albums[series_id]['tracks']:
                # Use cached tracks
                return YLEAPI.__albums[series_id]['tracks']
        album = {}
        tracklist = []
        albums, tracks = self.get_yle_item(offset=0, series=series_id)
        for item in tracks:
            track = tracks[item]
            album_id = track['album']
            if album_id:
                album = albums[album_id]
                track['album'] = album
            YLEAPI.__albums[series_id]['tracks'].append(track)
            tracklist.append(track)
        return tracklist
    
    def get_yle_image_url(self, program_id):
        url = None
        try:
            url = '{0}/{1}.png'.format(self.yle_image_url, program_id)
        except KeyError:
            logger.warning('No image for id {0}'.format(program_id))
        return url

    def get_yle_logo(self):
        return '{0}/{1}.png'.format(self.yle_image_url, 'v1445529201/17-2043254eef129bf7ac.jpg')

