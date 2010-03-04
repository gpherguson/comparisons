#!/usr/bin/env python

import io
import httplib
import httplib2
import lxml.etree
import lxml.html
import re
import StringIO
import sys
import time
import urllib2
import urlparse

# what we need to create the define/create tables...
from sqlalchemy import *
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import mapper
from sqlalchemy.orm import sessionmaker


DB_CONNECTION_URL = 'postgres://postgres:password@localhost/blogsearch'

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
URL_OPEN_TIMEOUT = 10 # in seconds

XML_NAMESPACE = 'http://www.w3.org/2005/Atom'
XHTML_NAMESPACE = "http://www.w3.org/1999/xhtml"

# look for the three feed types, in the order that we're most likely to encounter them: RSS, RDF, ATOM.
FEED_AUTODISCOVERY_XPATH = '/html/head/link[@rel="alternate" and (@type="application/rss+xml" or @type="application/rdf+xml" or @type="application/atom+xml")]/@href'

UA_HEADERS = {
        'User-Agent'        : 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-US; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5',
        'Accept'            : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language'   : 'en-us,en;q=0.5',
        # 'Accept-Encoding' : 'gzip,deflate',
        'Accept-Charset'    : 'UTF-8,*',
        'Keep-Alive'        : 300,
        'Connection'        : 'keep-alive'
    }


atom_feed_links = []
blog_page_urls = []
urls_for_db_list = []

def get_feed_url_from_blog(host_):
    try:
        request = urllib2.Request(_host, None, UA_HEADERS)          # build a request with all the extra-special headers...
        response = urllib2.urlopen(request, None, URL_OPEN_TIMEOUT) # open the request with a timeout so we don't wait forever...
        body = response.read()                                      # get the body...
        html_doc = lxml.html.document_fromstring(body)              # parse it to extract the link tags...

        # push the host url and the first feed link found since they're 'sposed to put the most important/relevant one first...
        feed_links = html_doc.xpath(FEED_AUTODISCOVERY_XPATH)

        urls_for_db_list.append([ _host, feed_links[0] ])

    except (httplib.HTTPException, IOError), e:
        print 'not readable.'
        if hasattr(e, 'reason'):
            print 'Could not reach', _host, e.reason
        elif hasattr(e, 'code'):
            print 'Server request failed. Error:', e.code


def add_feed_url_to_db(blogfeeds):
    ins_ = blogfeeds.insert()
    for blog_and_feed_urls_ in urls_for_db_list:
        blog_url_, feed_url_ = blog_and_feed_urls_

        engine.execute(ins_, blog_url = blog_url_, feed_url = feed_url_, created_on = time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime()), updated_at = time.strftime('%Y-%m-%d %H:%M:%S %Z', time.localtime()), enabled = True, language = 'en', longitude = 0.0, latitude = 0.0)
        print 'added.'


def blogsearch_google_filter(url): return url.find('blogsearch.google.com')
def not_blogsearch_google_filter(url): return not blogsearch_google_filter(url)


# set up the parsers
rss_parser = lxml.etree.XMLParser(
    recover           = True, # blowing chunks because of bad XML is a no-no.
    remove_blank_text = True  # strip useless whitespace.
)


h = httplib2.Http()
for k, v in TOPICS.iteritems():
    content = ''
    try:
        print 'retrieving', BASE_URL + k
        resp_, content = h.request(BASE_URL + k, 'GET')
    except IOError, e:
        if hasattr(e, 'reason'):
            print 'Cannot reach', BASE_URL
            print 'Reason:', e.reason
        elif hasattr(e, 'code'):
            print 'Connection failed.'
            print 'Error code:', e.code

        continue

    rss_root = lxml.etree.fromstring(content, rss_parser)

    # loop through the doc and get the links...
    atom_feed_links.extend(rss_root.xpath('//ns:link[@rel="alternate"]/@href', namespaces={'ns':XML_NAMESPACE})[1:])

    #for entry in (rss_root.xpath('//ns:entry', namespaces={'ns':XML_NAMESPACE})):
        # more links are hidden inside the content tag embedded in HTML...
        # [ lxml.etree.tostring(content) for content in rss_root.xpath('//ns:content/*|/text()', namespaces={'ns':XML_NAMESPACE}) ]

    # add all the <a>-tag hrefs from the embedded HTML...
    # [ atom_feed_links.append(a_tag) for a_tag in rss_root.xpath('//ns:a[@href]/@href', namespaces={'ns':XHTML_NAMESPACE}) ]
    atom_feed_links.extend( rss_root.xpath('//ns:a[@href]/@href', namespaces={'ns':XHTML_NAMESPACE}))



# no point in continuing if we don't have any links
if (not(atom_feed_links)):
    sys.exit(0)

# separate the non-google URLs from the google-based ones
blogsearch_google_urls = filter( blogsearch_google_filter,     atom_feed_links )
atom_feed_links        = filter( not_blogsearch_google_filter, atom_feed_links )
print len(atom_feed_links), 'atom URLs found'
print len(blogsearch_google_urls), 'google URLs found'

print 'set up the DB connection, load the tables, etc.'
engine = create_engine(DB_CONNECTION_URL, echo=True)

# create a place to store the table info...
metadata = MetaData()

# ...and get the table definitions.
# blogarticles = Table('blogarticles', metadata, autoload=True, autoload_with=engine)
blogfeeds = Table('blogfeeds', metadata, autoload=True, autoload_with=engine)

# tie the classes and definitions together...
# article_mapper = mapper(BlogArticle, blogarticles)
# feed_mapper = mapper(BlogFeed, blogfeeds)

# Session = sessionmaker(bind=engine)
# session = Session()
# session = sessionmaker(bind=engine)()

# walk through the list, and see if the host is already in the database...
# skipping existing entries, otherwise add it to the queue for further processing.
print 'push hosts into first queue.'
for _host in ([ urlparse.urlparse(_link).netloc for _link in set(atom_feed_links)]):
    print _host,

    s = select([blogfeed.c.blog_url], blog_url.c.blog_url == _host)
    # if (None == (session.query(BlogFeed.blog_url).filter_by(blog_url = _host).first())):
    if (None == s[blogfeed.c.blog_url]):
        blog_page_urls.append(_host)
        print 'queued.'
    # else:
    #     print 'already exists.'
