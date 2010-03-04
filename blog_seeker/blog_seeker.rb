#!/usr/bin/env ruby

require 'open-uri'
require 'timeout'
require 'thread'
require 'thwait'
require 'uri'

require 'rubygems'
require 'nokogiri'
require 'sequel'
require 'logger'

#
# define some constants
#
DB_CONNECTION_URL = 'postgres://postgres:password@localhost/blogsearch'
SHOW_SQL = true

BASE_ATOM_URL = 'http://blogsearch.google.com/blogsearch/feeds?bc_lang=en&hl=en&output=atom&topic='
TOPICS = {
  'p'  => 'Politics',
  'n'  => 'US',
  'w'  => 'World',
  'b'  => 'Business',
  't'  => 'Technology',
  'vg' => 'Video Games',
  'sc' => 'Science',
  'e'  => 'Entertainment',
  'm'  => 'Movies',
  'tv' => 'Television',
  's'  => 'Sports'
}

URL_OPEN_TIMEOUT = 10 # in seconds

XML_NAMESPACE   = 'http://www.w3.org/2005/Atom'
XHTML_NAMESPACE = 'http://www.w3.org/1999/xhtml'

# look in the (X)HTML for the three feed types, in the order that we're most
# likely to encounter them: RSS, RDF, ATOM.
FEED_AUTODISCOVERY_XPATH = '/html/head/link[@rel="alternate" and (@type="application/rss+xml" or @type="application/rdf+xml" or @type="application/atom+xml")]/@href'

# look in the ATOM file...
ATOM_ENTRY_PRIMARY_ARTICLE_HREF_XPATH = [ '//xmlns:link[@rel="alternate"]/@href', {'xmlns' => XML_NAMESPACE} ]
ATOM_ENTRY_CONTENT_A_HREF_XPATH       = [ '//xmlns:a[@href]/@href',               {'xmlns' => XML_NAMESPACE} ]
ATOM_ENTRY_CONTENT_ALL_RELATED_HREF_XPATH = [ '//xhtml:a[@class="allRelated" and @href]/@href', {'xhtml' => XHTML_NAMESPACE} ]

UA_HEADERS = {
  'User-Agent'        => 'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-US; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5',
  'Accept'            => 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
  'Accept-Language'   => 'en-us,en;q=0.5',
  # 'Accept-Encoding' => 'gzip,deflate',
  'Accept-Charset'    => 'UTF-8,*',
  'Keep-Alive'        => '300',
  'Connection'        => 'keep-alive'
}

#
# define some globals...
#
$blog_queue = Queue.new
$db_queue   = Queue.new

#
# set up resources...
#
DB = Sequel.connect(DB_CONNECTION_URL)
DB.loggers << Logger.new(STDOUT) if (SHOW_SQL)

group = ThreadsWait.new

#
# define some functions...
#

def get_page(url_)
  body = ''
  retries = 2

  begin
    Timeout::timeout(URL_OPEN_TIMEOUT) {
      request = open(host_, UA_HEADERS) # build a request with all the extra-special headers...
      body = request.read               # get the body...
    }
    return body
  rescue Timeout::Error
    retries -= 1
    raise OpenURI::HTTPError if (retries == 0)
    sleep 1
    retry
  rescue OpenURI::HTTPError => e
    print 'Could not reach ', host_, e, "\n"
    return nil
  end  
end

# Return the first auto-discovery feed URL from a blog. 
def get_feed_url_from_blog(host_)    
  body = get_page(host_)
  return if (!body)
  
  html_doc = Nokogiri::HTML(body) # parse it to extract the link tags...
  feed_link = html_doc.at(FEED_AUTODISCOVERY_XPATH)
  return URI.join(host_, feed_link.to_s).to_s rescue nil
end

# Move the urls from the $db_queue Queue and insert them into the database.
def add_feed_url_to_db()

  # point to the blogfeeds table...
  blogfeeds = DB[:blogfeeds]

  loop do
    blog_and_feed_urls_ = $db_queue.pop

    # we'll keep running until we find :DONE
    return if (blog_and_feed_urls_ == :DONE)

    blog_url, feed_url = blog_and_feed_urls_

    begin
      blogfeeds.insert(
        :blog_url   => blog_url,
        :feed_url   => feed_url,
        :created_on => Time.now,
        :updated_at => Time.now,
        :enabled    => true,
        :language   => 'en'
      )
    rescue Sequel::DatabaseError => e
      puts e
    end
  end
end

def get_link_hrefs_from_blog_search_atom_feed(url_)
  body = get_page(url_)
  feed_root = Nokogiri::XML(body)
  # feed_root.remove_namespaces!
  
  # get the primary article's href from the feed entries of the ATOM feeds.
  links = feed_root.xpath(ATOM_ENTRY_PRIMARY_ARTICLE_HREF_XPATH)[1 .. -1].map{ |i| i.to_s }
  
  # get all the <a>-tag hrefs pointing to individual blogs from the embedded HTML in the entries... (these are HTML pages)
  # [ links.append(_href) for _href in feed_root.xpath('//ns:a[@href]/@href', {'ns' => XHTML_NAMESPACES}) ] 
  feed_root.xpath(ATOM_ENTRY_CONTENT_A_HREF_XPATH).each { |_href| links.push(_href.to_s) }

  # return the "See all..." link's href. This would be a HTML page of more links but we're going to massage it to point to its ATOM representation.
  # see_all_links = [ '' + _href for _href in feed_root.xpath('//ns:a[@class="allRelated" and @href]/@href', {'ns' => XHTML_NAMESPACES}) ]
  see_all_links = feed_root.xpath(ATOM_ENTRY_CONTENT_ALL_RELATED_HREF_XPATH).map{ |i| i.to_s }
  return { :links => links, :see_all_links => see_all_links }
end

def get_url_host(url_)
  u = URL.parse(url_)
  return "#{u.scheme}://#{u.host}"
  rescue Exception
    return nil
end

#
# start processing...
#

# add the blog topics to the queue...
TOPICS.keys.each do |_k| 
    hash_element = get_link_hrefs_from_blog_search_atom_feed(BASE_ATOM_URL + _k)
    $blog_queue.push(hash_element) if (hash_element) 
end
$blog_queue.push(:DONE)

# walk through the URLs retrieved from Google's blog search pages...
blog_queue_done = false
(1 .. 5).map do |i|
  Thread.new("blog_url_processor #{i}") do |name|
    begin
      urls = $blog_queue.pop
      
      blog_queue_done = true if (urls == :DONE)
      last if (blog_queue_done)
      
      links, see_all_links = urls
      
      # these are links to individual blogs so push them onto the queue for
      # insertion into the database.
      links.each do |i|
        url = get_url_host(i)
        $feed_queue.push(url) if (url)
      end
      
      # these are links to pages needing additional processing...
      see_all_links.each do |i|
        url = get_url_host(i)
        $feed_queue.push(url) if (url)
      end
    end
  end
end

$db_queue.push(:DONE)

add_feed_url_to_db()
print 'Done'

