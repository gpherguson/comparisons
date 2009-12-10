#!/usr/bin/env python

import io
import lxml.etree
import re
import StringIO
import urllib2
import urlparse

import pdb

BASE_URL = 'http://blogsearch.google.com/blogsearch/feeds?bc_lang=en&hl=en&output=atom&topic='
TOPICS = {
    'p':  'Politics',
    'n':  'US',
    'w':  'World',
    'b':  'Business',
    't':  'Technology',
    'vg': 'Video Games',
    'sc': 'Science',
    'e':  'Entertainment',
    'm':  'Movies',
    'tv': 'Television',
    's':  'Sports'
}
URL_OPEN_TIMEOUT = 10

XML_NAMESPACE = 'http://www.w3.org/2005/Atom'
XHTML_NAMESPACE = "http://www.w3.org/1999/xhtml"

# set up the parser
rss_parser = lxml.etree.XMLParser(
    recover           = True, # blowing chunks because of bad XML is a no-no.
    remove_blank_text = True  # strip useless whitespace.
) 
html_parser = lxml.etree.HTMLParser()

links = []

# walk through the list of topics and retrieve the feed...
for k, v in TOPICS.iteritems():
    try:
        rss_root = lxml.etree.parse(BASE_URL + k, rss_parser)
    except IOError, e:
        if hasattr(e, 'reason'):
            print 'Cannot reach {0}'.format(BASE_URL)
            print 'Reason:', e.reason
        elif hasattr(e, 'code'):
            print 'Connection failed.'
            print 'Error code:', e.code


    # loop through the doc and get the links...
    links.append(rss_root.xpath('//ns:link[@rel="alternate"]/@href', namespaces={'ns':XML_NAMESPACE})[0])

    # pdb.set_trace()

    for entry in (rss_root.xpath('//ns:entry', namespaces={'ns':XML_NAMESPACE})):

        # more links are hidden inside the content tag embedded in HTML...
        content_html = entry.xpath('ns:content/*|/text()', namespaces={'ns':XML_NAMESPACE})
        
        # add all the <a>-tag hrefs from the embedded HTML...
        [ links.append(a_tag) for a_tag in entry.xpath('//ns:a[@href]/@href', namespaces={'ns':XHTML_NAMESPACE}) ] 


# walk the links and retrieve the hostnames, because that's all we want.
hosts = sorted(set([ urlparse.urlparse(_link).netloc for _link in links ]))

# show what we got...
print "\n".join(hosts)

