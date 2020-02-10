"""Searches wikipedia and returns first sentence of article
Scaevolus 2009"""

import re

import requests

from cloudbot import hook
from cloudbot.util import formatting
from cloudbot.util.http import parse_xml

api_prefix = "http://en.wikipedia.org/w/api.php"
search_url = api_prefix + "?action=opensearch&format=xml"
random_url = api_prefix + "?action=query&format=xml&list=random&rnlimit=1&rnnamespace=0"

paren_re = re.compile(r'\s*\(.*\)$')


@hook.command("wiki", "wikipedia")
def wiki(text, reply):
    """<phrase> - Gets first sentence of Wikipedia article on <phrase>."""

    try:
        request = requests.get(search_url, params={'search': text.strip()})
        request.raise_for_status()
    except (requests.exceptions.HTTPError, requests.exceptions.ConnectionError) as e:
        reply("Could not get Wikipedia page: {}".format(e))
        raise

    x = parse_xml(request.text)

    ns = '{http://opensearch.org/searchsuggest2}'
    items = x.findall(ns + 'Section/' + ns + 'Item')

    if not items:
        if x.find('error') is not None:
            return 'Could not get Wikipedia page: %(code)s: %(info)s' % x.find('error').attrib

        return 'No results found.'

    def extract(item):
        return [item.find(ns + i).text for i in
                ('Text', 'Description', 'Url')]

    title, desc, url = extract(items[0])

    if 'may refer to' in desc:
        title, desc, url = extract(items[1])

    title = paren_re.sub('', title)

    if title.lower() not in desc.lower():
        desc = title + desc

    desc = ' '.join(desc.split())  # remove excess spaces
    desc = formatting.truncate(desc, 200)

    return '{} :: {}'.format(desc, requests.utils.quote(url, ':/%'))
