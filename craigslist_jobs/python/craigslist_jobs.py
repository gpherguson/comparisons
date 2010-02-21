#!/usr/bin/env python

from datetime import datetime
from lxml import etree
import re
import urllib
import rsslib

JOBS_URL = 'http://phoenix.craigslist.org/sof/index.html'
HREF_STR = 'phoenix.craigslist.org/evl/sof/'

def add_item(l):
    body = urllib.urlopen(l).read()
    post_date = re.findall( 'Date:\s+(\S+,?\s+\S+\s+\S+)<br>', body, re.IGNORECASE )[0] 
    html = etree.HTML(body)
    h2 = html.xpath('//h2/text()')[0]

    item = rsslib.Item()
    item.link = l
    item.description = ''
    item.title = h2
    item.pubDate = datetime.strptime(post_date, '%Y-%m-%d, %H:%M%p %Z')
    return item

body = urllib.urlopen(JOBS_URL).read()
html = etree.HTML(body)
item_list = [ add_item(l) for l in html.xpath('//a[contains( @href, "%s")]/@href' % HREF_STR) ]

rss = rsslib.RSS()
rss.channel.link = JOBS_URL
rss.channel.title = "Craig's List jobs"
rss.channel.description = "Software jobs of interest at Craig's List"
for l in item_list:
    rss.addItem(l)

print "Content-type: application/rss+xml"
print
print rss.write()
