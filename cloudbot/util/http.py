# convenience wrapper for urllib & friends
import base64
import binascii
import hmac
import json
import random
import string
import time
import urllib
import urllib.request as request
import urllib.parse as parse

from hashlib import sha1
from urllib.parse import quote, quote_plus as _quote_plus
from urllib.error import HTTPError, URLError

from lxml import etree, html
from bs4 import BeautifulSoup

from http.cookiejar import CookieJar
from html.parser import HTMLParser

ua_firefox = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.6) ' \
             'Gecko/20070725 Firefox/2.0.0.6'

jar = CookieJar()
h = HTMLParser()


def get(*args, **kwargs):
    return open(*args, **kwargs).read()


def get_html(*args, **kwargs):
    return html.fromstring(get(*args, **kwargs))


def get_xml(*args, **kwargs):
    return etree.fromstring(get(*args, **kwargs))


def get_json(*args, **kwargs):
    return json.loads(get(*args, **kwargs))


def get_soup(*args, **kwargs):
    return BeautifulSoup(get(*args, **kwargs), 'lxml')


def open(url, params=None, headers=None, data=None, timeout=10, get_method=None,
         cookies=False, auth=None, auth_keys=None, oauth=False, oauth_keys=None, **kwargs):

    if params is None:
        params = {}

    params.update(kwargs)

    url = prepare_url(url, params)

    _request = request.Request(url, data)

    if get_method is not None:
        _request.get_method = lambda: get_method

    if headers is not None:
        for header_key, header_value in headers.iteritems():
            _request.add_header(header_key, header_value)

    if 'User-Agent' not in _request.headers:
        _request.add_header('User-Agent', ua_firefox)

    if auth:
        base64string = base64.b64encode('%s:%s' % (auth_keys['username'], auth_keys['password']))
        _request.add_header("Authorization", "Basic %s" % base64string)

    if oauth:
        nonce = oauth_nonce()
        timestamp = oauth_timestamp()
        api_url, req_data = string.split(url, "?")
        unsigned_request = oauth_unsigned_request(nonce, timestamp, req_data, oauth_keys['consumer'], oauth_keys['access'])

        signature = oauth_sign_request("GET", api_url, req_data, unsigned_request, oauth_keys['consumer_secret'], oauth_keys['access_secret'])

        header = oauth_build_header(nonce, signature, timestamp, oauth_keys['consumer'], oauth_keys['access'])
        _request.add_header('Authorization', header)

    if cookies:
        opener = request.build_opener(request.HTTPCookieProcessor(jar))
    else:
        opener = request.build_opener()
    return opener.open(_request, timeout=timeout)


def prepare_url(url, queries):
    if queries:
        scheme, netloc, path, query, fragment = parse.urlsplit(url)

        query = dict(parse.parse_qsl(query))
        query.update(queries)
        query = urllib.urlencode(dict((to_utf8(key), to_utf8(value))
                                  for key, value in query.iteritems()))

        url = parse.urlunsplit((scheme, netloc, path, query, fragment))

    return url


def to_utf8(s):
    if isinstance(s, unicode):
        return s.encode('utf8', 'ignore')
    else:
        return str(s)


def quote_plus(s):
    return _quote_plus(to_utf8(s))


def oauth_nonce():
    return ''.join([str(random.randint(0, 9)) for i in range(8)])


def oauth_timestamp():
    return str(int(time.time()))


def oauth_unsigned_request(nonce, timestamp, req, consumer, token):
    d = { 'oauth_consumer_key':consumer,
          'oauth_nonce':nonce,
          'oauth_signature_method':'HMAC-SHA1',
          'oauth_timestamp':timestamp,
          'oauth_token':token,
          'oauth_version':'1.0' }

    d.update(dict(parse.parse_qsl(req)))
    unsigned_req = ''

    for x in sorted(d, key=lambda key: key):
        unsigned_req += x + "=" + d[x] + "&"

    unsigned_req = quote(unsigned_req[:-1])
    return unsigned_req


def oauth_build_header(nonce, signature, timestamp, consumer, token):
    d = { 'oauth_consumer_key':consumer,
          'oauth_nonce':nonce,
          'oauth_signature':signature,
          'oauth_signature_method':'HMAC-SHA1',
          'oauth_timestamp':timestamp,
          'oauth_token':token,
          'oauth_version':'1.0' }

    header='OAuth '

    for x in sorted(d, key=lambda key: key):
        header += x + '="' + d[x] + '", '

    return header[:-1]


def oauth_sign_request(method, url, params, unsigned_request, consumer_secret, token_secret):
    key = consumer_secret + "&" + token_secret

    base = method + "&" + quote(url, '') + "&" + unsigned_request

    hash = hmac.new(key, base, sha1)

    signature = quote(binascii.b2a_base64(hash.digest())[:-1])

    return signature


def parse_soup(text, features=None, **kwargs):
    if features is None:
        features = 'lxml'

    return BeautifulSoup(text, features=features, **kwargs)


def parse_xml(text):
    return etree.fromstring(text, parser=parser)


def get_title(url, tag="title"):
    return h.unescape(get_soup(url).find(tag).text)

