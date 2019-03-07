from __future__ import unicode_literals
import logging
import os
import pykka
import base64
import requests
import isodate
from mopidy import models
from mopidy.models import Ref, Artist, Album, Track
from mopidy import httpclient
from Crypto.Cipher import AES
from . import Extension

logger = logging.getLogger(__name__)

class YLEAPI:
    yle_url = 'https://external.api.yle.fi/v1'
    yle_image_url = 'http://images.cdn.yle.fi/image/upload'
    unplayableCategories = ['5-162', '5-164', '5-226', '5-228']
    radioCategory = '5-200'
    __categories = []
    __tracks = {}
    
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
        return YLEAPI.__categories

    def get_requests_session(self):
        proxy = httpclient.format_proxy(self.__config['proxy'])
        full_user_agent = httpclient.format_user_agent('%s/%s' % (self.__dist_name, self.__version))
        
        session = requests.Session()
        session.proxies.update({'http': proxy, 'https': proxy})
        session.headers.update({'user-agent': full_user_agent})
        
        return session

    def get_yle_item(self, offset, query=None, category=None, limit=None, series=None):
        parameters = ['availability=ondemand', 'mediaobject=audio']
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
        radio_id = None
        for item in categories:
            unplayable = False
            if 'broader' not in item:
                if item['key'] == 'radio':
                    radio_id = item['id']
                    break
        if not radio_id:
            return result
        for item in categories:
            if 'broader' in item:
                id = item['id']
                title = item['title'][self.__config['yle']['language']]
                result.append(Ref.directory(name=title, uri='yle:category:{0}'.format(id)))
#            if 'broader' in item:
#                if item['broader']['id'] == radio_id:
#                    id = item['id']
#                    title = item['title'][self.__config['yle']['language']]
#                    result.append(Ref.directory(name=title, uri='yle:category:{0}'.format(id)))
        return result

    def parse_items(self, items):
        result = []
        albums = {}
        tracks = {}
  #      logger.warning('TRACKS: {0}'.format(items))
        for item in items:
            id = item['id']
#            logger.warning('ID: {0}'.format(item['image']))
            if 'publicationEvent' in item:
                try:
                    title = item['title'][self.__config['yle']['language']]
                except KeyError:
                    # Not for this language
                    continue
                event = item['publicationEvent'][0]
                if event['temporalStatus'] == 'currently' and event['type'] == 'OnDemandPublication':
                    media_id = event['media']['id']
                    if not event['media']['type'] == 'AudioObject':
                        logger.warning('No audio available in the program')
                        continue
                    tracks[id] = Ref.track(name=title, uri='yle:track:{0}:{1}'.format(id, media_id))
                    YLEAPI.__tracks[id] = item
                    continue
            if 'partOfSeries' in item:
#                logger.warning('ITEM1: {0}'.format(item['partOfSeries']))
                id = item['partOfSeries']['id']
                try:
                    title = item['partOfSeries']['title'][self.__config['yle']['language']]
                except KeyError:
                    # Not for this language
                    continue
                albums[id] = Ref.album(name=title, uri='yle:series:{0}'.format(id))
#            else:
#                logger.warning('IS')
#                try:
#                    title = item['title'][self.__config['yle']['language']]
#                except KeyError:
#                    # Not for this language
#                    continue
#                tracks[id] = Ref.track(name=title, uri='yle:track:{0}'.format(id))
#                YLEAPI.__tracks[id] = item
                
        for i in albums:
            result.append(albums[i])
#            logger.warning('ALBUM: {0}'.format(i))
        for i in tracks:
            result.append(tracks[i])
#            logger.warning('TRACK: {0}'.format(id))
            
        # if 'partOfSeries' in items:
        #     # This is an 'album'
        #     logger.warning('ALBUM2: {0}'.format(items['partOfSeries']))
        #     logger.warning(items['id'])
        #     logger.warning(items['title'])
        #     continue
        #     id = items['id']
        #     try:
        #         title = items['title'][self.__config['yle']['language']]
        #     except KeyError:
        #         # Not for this language
        #         continue
        #     result.append(Ref.album(name=title, uri='yle:album:{0}'.format(id)))
        # else:
        #     # This is a 'track'
        #     logger.warning(items['id'])
        #     logger.warning(items['title'])
        #     id = items['id']
        #     continue
        #     try:
        #         title = items['title'][self.__config['yle']['language']]
        #     except KeyError:
        #         # Not for this language
        #         continue
        #     for event in items['publicationEvent']:
        #         logger.warning(event)
        #         result.append(Ref.track(name=title, uri='yle:track:{0}'.format(id)))
        #         YLEAPI.__tracks[id] = items
        #         continue
        return result
    
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

    def get_yle_track_info(self, program_id, uri):
        if YLEAPI.__tracks:
            if program_id in YLEAPI.__tracks:
                #logger.warning('MEDIA: {0}'.format(YLEAPI.__tracks[program_id]['publicationEvent'][0]['media']))
                item = YLEAPI.__tracks[program_id]
                try:
                    title = item['title'][self.__config['yle']['language']]
                except KeyError:
                    # Not in this language
                    return None
                media = item['publicationEvent'][0]['media']
                duration = media['duration']
                logger.info('LENGTH: {0}'.format(isodate.parse_duration(duration).microseconds))
                return models.Track(name=title, uri=uri, length=1000 * isodate.parse_duration(duration).seconds)
        return None
    
    def get_yle_image_url(self, program_id):
        url = None
        try:
            image_id = YLEAPI.__tracks[program_id]['image']['id']
            url = '{0}/{1}.jpg'.format(self.yle_image_url, image_id)
        except KeyError:
            logger.warning('No image for id {0}'.format(program_id))
        return url
    
