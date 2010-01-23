#!/usr/bin/env python

"""
Code to read Guitar Center's used equipment feed, parse the article titles, and print them as a HTML page.
"""

import operator
import re
import time
import urllib2
import urlparse
import xml.dom.minidom

import pdb

BASE_URL = 'http://used.guitarcenter.com/usedGear/'
FEED_URL = 'usedListings_rss.xml'
URL_OPEN_TIMEOUT = 10

def get_title(_item):
    """ get the title for the element. """
    return _item.getElementsByTagName('title')[0].childNodes[0].nodeValue

def get_description(_item):
    """ get the description for the element. """
    return _item.getElementsByTagName('description')[0].childNodes[0].nodeValue

def get_link(_item):
    """ get the link for the element. """
    return _item.getElementsByTagName('link')[0].childNodes[0].nodeValue

def get_publish_date(_item):
    """ get the publish date for the element. """
    return _item.getElementsByTagName('pubDate')[0].childNodes[0].nodeValue

def sortkeypicker(keynames):
    """ from: http://stackoverflow.com/questions/1143671/python-sorting-list-of-dictionaries-by-multiple-keys/1143719#1143719 """
    negate = set()
    for i, k in enumerate(keynames):
        if k[:1] == '-':
            keynames[i] = k[1:]
            negate.add(k[1:])
    def getit(adict):
       composite = [adict[k] for k in keynames]
       for i, (k, v) in enumerate(zip(keynames, composite)):
           if k in negate:
               composite[i] = -v
       return composite
    return getit

    
try:
    feedbody = urllib2.urlopen(BASE_URL + FEED_URL, None, URL_OPEN_TIMEOUT).read()
except IOError, e:
    if hasattr(e, 'reason'):
        print 'Cannot reach {0}'.format(BASE_URL)
        print 'Reason:', e.reason
    elif hasattr(e, 'code'):
        print 'Connection failed.'
        print 'Error code:', e.code

dom1 = xml.dom.minidom.parseString(feedbody)

feed_description = get_description(dom1)
feed_link        = get_link(dom1)
feed_title       = get_title(dom1)

# pdb.set_trace()

# gather the lines...
lines = []
for item in (dom1.getElementsByTagName('item')):
    item_description = get_description(item)
    item_link        = get_link(item)
    item_pub_date    = get_publish_date(item)
    item_title       = get_title(item)

    u = urlparse.urljoin(BASE_URL, item_link)
    
    # The time stamp is really a date, so we'll truncate the time portion.
    parsed_date = time.strptime(item_pub_date[0:16], '%a, %d %b %Y')
    
    lines.append({
        'description': item_description,
        'link': u,
        'pubdate': time.strftime('%m/%d/%Y', parsed_date),
        'type': item_title
    }) 

# sort the lines...
sorted_lines = sorted(lines, key=sortkeypicker(['type', 'description']))

print '<html><head><title>{0}</title>'.format(feed_title)
# add CSS or JavaScript here.
print '<style type="text/css">'
print 'table { background-color: #efefef; }'
print 'tr { vertical-align: top; }'
print 'th { text-align: left; background-color: #dfdfdf; border: 1px solid #cfcfcf; }'
print '</style>'
print '</head>'
print '<body><h3><a href="{0}">{1}</a></h3>'.format(feed_link, feed_title)
print '<h4>{0}</h4>'.format(feed_description)
print '<table>'
print '<tr><th>Published</th><th>Type</th><th>Description</th></tr>'

# show the lines...
for line in sorted_lines:
    print '<tr><td>{0}</td><td><a href="{1}">{2}</a></td><td>{3}</td></tr>'.format(
        line['pubdate'],
        line['link'],
        line['type'],
        line['description']
    )

print '</table></body></html>'

dom1.unlink()
