#!/usr/bin/env python

"""
1.  Iterate through the list of ATOM feeds for Google's blog-search results.
Push each URL onto the blog_links_q queue.

2.  google_atom_worker() gets called in a thread and pops a url off the
blog_search_q queue, requests the url using get_page(), and pushes the
resulting response and content onto the resp_q queue as a list.

3.  db_worker() get called in a single-thread and retrieves an entry from the
resp_q queue. That entry consists of the HTTP response and content of a
get_page() call. The content is parsed to extract the link hrefs from the feed
"""

import httplib
import httplib2
import lxml.etree
import lxml.html
from Queue import Queue
import time
from threading import Thread
#import urllib2
from urlparse import urljoin

# from sqlalchemy import MetaData
# from sqlalchemy import create_engine
from sqlalchemy import *
from sqlalchemy.exceptions import *

NUM_PROCESSES = 20
REQUEST_TIMEOUT = 10

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

XML_NAMESPACES = {'ns':'http://www.w3.org/2005/Atom'}
XHTML_NAMESPACES = {'ns':'http://www.w3.org/1999/xhtml'}

SEE_ALL_HREFS_XPATH = '//ns:a[@class="allRelated" and @href]/@href'

# look for the three feed types, in the order that we're most likely to
# encounter them: RSS, RDF, ATOM.
FEED_AUTODISCOVERY_XPATH = '/html/head/link[@rel="alternate" and (@type="application/rss+xml" or @type="application/rdf+xml" or @type="application/atom+xml")]/@href'

UA_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-US; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us,en;q=0.5',
        'Accept-Charset': 'UTF-8,*',
        'Keep-Alive': '300',
        'Connection': 'keep-alive'
        # 'Accept-Encoding': 'gzip,deflate',
    }

def add_additional_feeds_to_db(_url):
    """
    Insert a url pointing to additional urls into the additional_feeds table.
    """
    print 'inserted', _url
    try:
        conn.execute(additional_feeds_insert, url=_url)
    except (Exception, IntegrityError) as e:
        print e

    return

def add_feed_to_db(_blog_url):
    """
    Insert a feed into the database.
    """
    print 'inserted', _blog_url
    try:
        conn.execute(feed_insert, blog_url=_blog_url, feed_url=None, enabled=False, language='en')
    except (Exception, IntegrityError ) as e:
        print e

    return

def get_page(_url):
    """
    Returns the response, content from the page.
    """
    try:
        return httplib2.Http(timeout=REQUEST_TIMEOUT).request(_url, headers=UA_HEADERS)
    except Exception as err:
        print err, 'reading', _url
        return None, None
     
def get_all_related_feeds_hrefs(_xml_tree):
    """
    Returns all the hrefs in the page that point to all the other "See all"
    blogs.
    """
    return _xml_tree.xpath(SEE_ALL_HREFS_XPATH)

def google_atom_worker():
    """
    Get a url from the queue and push the results of retrieving the
    document onto resp_q.
    """
    while True:
        _url = blog_search_q.get()
        if (_url):
            try:
                resp_q.put(get_page(_url))
            except Exception as e:
                print e
        blog_search_q.task_done()

def blog_reader_worker():
    """
    Retrieves a blog url, extracts the primary feed URL and pushes it onto the
    blog_links_q queue.
    """
    while True:
        _url = blog_links_q.get()
        if (_url):
            try:
                _resp, _body = get_page(_url)
                if (_body):
                   _href = get_feed_url_from_blog(_body) 
                  feed_url = urljoin(_resp['content-location'], _href)
                  add_feed_to_db(_resp['content-location'], feed_url)
            except Exception as e:
                print e


def get_feed_url_from_blog(body):
    """
    Get the first feed url from the host if it exists.
    """
    try:
        html_doc = lxml.html.document_fromstring(body) # parse it to extract the link tags...

        # push the host url and the first feed link found since they're 'sposed
        # to put the most important/relevant one first...
        feed_links = html_doc.xpath(FEED_AUTODISCOVERY_XPATH)

        try:
            return feed_links[0]
        except Exception:
            return None
        
    except (httplib.HTTPException, IOError), e:
        if hasattr(e, 'reason'):
            print e.reason
        elif hasattr(e, 'code'):
            print e.code
    return

def get_link_hrefs_from_feed(content):
    rss_root = lxml.etree.fromstring(content, rss_parser)

    # get the links...
    links = rss_root.xpath('//ns:link[@rel="alternate"]/@href', namespaces=XML_NAMESPACES)[1:]

    # for entry in (rss_root.xpath('//ns:entry', namespaces=XML_NAMESPACES)):
        # add all the <a>-tag hrefs from the embedded HTML...
        # [ links.append(_href) for _href in entry.xpath('//ns:a[@href]/@href', namespaces=XHTML_NAMESPACES) ] 
    [ links.append(_href) for _href in rss_root.xpath('//ns:a[@href]/@href', namespaces=XHTML_NAMESPACES) ] 
    
    # return the "Also see" links after converting them to strings.
    see_also_links = [ '' + _href for _href in rss_root.xpath('//ns:a[@class="allRelated" and @href]/@href', namespaces=XHTML_NAMESPACES) ]
    return { 'links': links, 'see_also_links': see_also_links }

def db_worker():
    """ Get a request from the queue and try to insert it into the table. """
    while True:
        _resp, _body = resp_q.get()
        if (_body):
            # feed_url = get_feed_url_from_blog(_body)
            # feed_url = urljoin(_resp['content-location'], feed_url)
            links_to_process = get_link_hrefs_from_feed(_body)
            for _href in links_to_process['links']:
                if (_resp and _resp['content-location'] and _href):
                    feed_url = urljoin(_resp['content-location'], _href)
                    # add_feed_to_db(_resp['content-location'])
                    add_feed_to_db(feed_url)
                else:
                    print _resp['content-location'], 'missing href'

            for _href in links_to_process['see_also_links']:
                add_additional_feeds_to_db(_href)

        resp_q.task_done()
 

# set up the parser
rss_parser = lxml.etree.XMLParser(
    recover           = True, # blowing chunks because of bad XML is a no-no.
    remove_blank_text = True  # strip useless whitespace.
) 

# set up the database connection...
engine = create_engine('postgres://postgres:password@localhost/blogsearch', echo=False)
meta = MetaData()
meta.reflect(bind=engine)
feeds            = meta.tables['blogfeeds']
additional_feeds = meta.tables['additional_feeds']
feed_insert             = feeds.insert().values(blog_url='blog_url', feed_url=None, enabled=False, language='en')
additional_feeds_insert = additional_feeds.insert().values(url='blog_url')
conn = engine.connect()

# Create queues for the primary blog-search ATOM feeds from Google.
blog_search_urls_q  = Queue() 

# Create queues for blog URLs extracted from each ATOM feed.
#
# Each entry contains a dictionary consisting of the response and content after
# reading the blog-search ATOM feeds.
blog_links_q = Queue() 

# Create a queue for the blog feeds to be inserted into the database after
# looking at the blog and getting its primary feed URL.
resp_q = Queue() 

for _i in range(NUM_PROCESSES):
    t = Thread(target=google_atom_worker)
    t.setDaemon(True)
    t.start()
    t = Thread(target=blog_reader_worker)
    t.setDaemon(True)
    t.start()

# and 1 thread to handle the database writes of the urls found in the
# blog-search feeds...
for _i in range(1):
    t = Thread(target=db_worker)
    t.setDaemon(True)
    t.start()

for _k in TOPICS.keys():
    blog_search_q.put(BASE_URL + _k)

blog_search_q.join()  # block until all URL reading tasks are done
resp_q.join() # block until all DB writes finish

