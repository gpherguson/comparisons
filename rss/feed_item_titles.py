#!/usr/bin/env python

"""
Code to read Guitar Center's used equipment feed, parse the article titles, and print them as a HTML page.

lxml.html.builder can be used to generate HTML, so *maybe* this will get equivalent code to the other versions using that. *maybe*
"""

from lxml import etree
import operator
import re
import time
import urlparse


BASE_URL = 'http://used.guitarcenter.com/usedGear/'
FEED_URL = 'usedListings_rss.xml'

HTML_ESCAPE_TABLE = {
    "&": "&amp;",
    '"': "&quot;",
    "'": "&apos;",
    ">": "&gt;",
    "<": "&lt;",
    }

def html_escape(text):
    """Produce entities within text."""
    return ''.join(HTML_ESCAPE_TABLE.get(c, c) for c in text)

def get_title(_item):
    """ get the title for the element. """
    return _item.xpath('title/text()')[0]

def get_description(_item):
    """ get the description for the element. """
    return _item.xpath('description/text()')[0]

def get_link(_item):
    """ get the link for the element. """
    return _item.xpath('link/text()')[0]

def get_publish_date(_item):
    """ get the publish date for the element. """
    return _item.xpath('pubDate/text()')[0]

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

    
dom1 = etree.parse(BASE_URL + FEED_URL)

feed_description = '' + get_description(dom1.xpath('//channel')[0])
feed_link        = '' + get_link(dom1.xpath('//channel')[0])
feed_title       = '' + get_title(dom1.xpath('//channel')[0])

# gather the lines...
lines = []
for item in (dom1.xpath('//item')):
    item_description = get_description(item)
    item_link        = get_link(item)
    item_pub_date    = get_publish_date(item)
    item_title       = get_title(item)

    u = urlparse.urljoin(BASE_URL, item_link)
    
    # The time stamp is really a date, so we'll truncate the time portion.
    parsed_date = time.strptime(item_pub_date[0:16], '%a, %d %b %Y')
    
    lines.append({
        'description': '' + item_description,
        'link': '' + u,
        'pubdate': time.strftime('%m/%d/%Y', parsed_date),
        'type': '' + item_title
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
        html_escape(line['description'])
    )

print '</table></body></html>'

