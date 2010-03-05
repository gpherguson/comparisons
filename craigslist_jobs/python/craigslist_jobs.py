#!/usr/bin/env python

"""
Code to read Craigs List jobs for a given city, returning a RSS feed of jobs
matching the given keywords. 
"""

from datetime import datetime
from lxml import html
import re
import rsslib


# modify these as needed
JOBS_URL = 'http://phoenix.craigslist.org/sof/index.html'
HREF_STR = 'phoenix.craigslist.org/evl/sof/'
KEYWORDS = frozenset(['perl', 'ruby', 'python', 'postgres', 'postgresql'])

def add_item(link, desc, title, date):
    """
    Grab a page and extract what we need. Ignore it if it doesn't have any of
    our desired keywords.
    """
    item = rsslib.Item()
    item.link = link
    item.description = 'Keywords: ' + desc
    item.title = title
    item.pubDate = datetime.strptime(date, '%Y-%m-%d, %H:%M%p %Z')
    return item

# initialize the feed...
rss = rsslib.RSS()
rss.channel.link = JOBS_URL
rss.channel.title = "Craig's List jobs"
rss.channel.description = "Software jobs of interest at Craig's List"

# get the page from Craig's List...
html_doc = html.parse(JOBS_URL)

# loop through the anchors matching the city, extracting the hrefs. Parse those
# pages and get the fields we need...
item_list = []
for l in html_doc.xpath('//a[contains( @href, "%s")]/@href' % HREF_STR):
    _h = html.parse(l)
    body = _h.xpath('//body')[0].text_content()
    post_date = re.findall( 'Date:\s+(\S+,?\s+\S+\s+\S+)', body, re.IGNORECASE )[0]
    h2 = _h.xpath('//h2/text()')[0]
    keyword_hits = set([ hit for hit in body.split() if (hit.lower() in KEYWORDS) ])
    if (keyword_hits == set([])):
        continue
    rss.addItem(add_item(l, ', '.join(keyword_hits), h2, post_date))

# output the feed...
print "Content-type: application/rss+xml"
print
print rss.write()
