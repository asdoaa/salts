"""
    SALTS XBMC Addon
    Copyright (C) 2014 tknorris

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import scraper
import re
import urlparse
import xbmcaddon
import xbmc
import base64
import urllib
from salts_lib.db_utils import DB_Connection
from salts_lib import GKDecrypter
from salts_lib import log_utils
from salts_lib.constants import VIDEO_TYPES
from salts_lib.constants import QUALITIES

BASE_URL = 'http://hdlord.com'

class HDLord_Scraper(scraper.Scraper):
    base_url=BASE_URL
    def __init__(self, timeout=scraper.DEFAULT_TIMEOUT):
        self.timeout=timeout
        self.db_connection = DB_Connection()
        self.base_url = xbmcaddon.Addon().getSetting('%s-base_url' % (self.get_name()))
   
    @classmethod
    def provides(cls):
        return frozenset([VIDEO_TYPES.MOVIE])
    
    @classmethod
    def get_name(cls):
        return 'HDLord'
    
    def resolve_link(self, link):
        return link
    
    def format_source_label(self, item):
        label='[%s] %s (%s views) ' % (item['quality'], item['host'], item['views'])
        return label
    
    def get_sources(self, video):
        source_url=self.get_url(video)
        hosters = []
        if source_url:
            url = urlparse.urljoin(self.base_url, source_url)
            html = self._http_get(url, cache_limit=.5)
            for match in re.finditer('proxy\.link\s*=\s*([^"]+)', html):
                proxy_link = match.group(1)
                proxy_link = proxy_link.split('*', 1)[-1]
                stream_url = GKDecrypter.decrypter(198,128).decrypt(proxy_link, 'uhaVp8Gvykcy1bFQafBR','ECB').split('\0')[0]
                host = urlparse.urlsplit(stream_url).hostname
                if host and stream_url not in (hoster['url'] for hoster in hosters):
                    hoster = {'multi-part': False, 'url': stream_url, 'class': self, 'quality': QUALITIES.HD, 'host': host, 'rating': None, 'views': None, 'direct': True}
                    hosters.append(hoster)
         
        return hosters

    def get_url(self, video):
        return super(HDLord_Scraper, self)._default_get_url(video)
    
    def search(self, video_type, title, year):
        search_url = urlparse.urljoin(self.base_url, '/browse_items.php')
        search_url += '?' + urllib.urlencode({'title': title, 'year': year})
        data = {'keyword': '%s %s' % (title, year)}
        html = self._http_get(search_url, data=data, cache_limit=.25)
        
        results=[]
        pattern = "href='([^']+)'\s+class='item_result_title'>\s*([^<]+)\s+\((\d{4})\)"
        for match in re.finditer(pattern, html, re.DOTALL):
            url, match_title, match_year = match.groups('')
            result = {'url': url.replace(self.base_url,''), 'title': match_title, 'year': match_year}
            results.append(result)
        return results
    
    def _http_get(self, url, data=None, cache_limit=8):
        return super(HDLord_Scraper, self)._cached_http_get(url, self.base_url, self.timeout, data=data, cache_limit=cache_limit)