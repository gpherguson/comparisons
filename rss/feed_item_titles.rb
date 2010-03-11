#!/usr/bin/env ruby -w

#
# Code to read Guitar Center's used equipment feed, parse the article titles, and print them as a HTML page.
#

require 'rubygems'
require 'cgi'
require 'open-uri'
require 'nokogiri'
require 'time'
require 'uri'

BASE_URL = 'http://used.guitarcenter.com/usedGear/'
FEED_URL = 'usedListings_rss.xml'
URL_OPEN_TIMEOUT = 10

# get the title for the element.
def get_title(_item)
  return _item.at('title').text
end

# get the description for the element.
def get_description(_item)
  return _item.at('description').text
end

# get the link for the element.
def get_link(_item)
  return _item.at('link').text
end

# get the publish date for the element.
def get_publish_date(_item)
  return _item.at('pubDate').text
end


begin
  feedbody = open(BASE_URL + FEED_URL).read
rescue => e
  STDERR.puts e.to_s
  exit
end

dom1 = Nokogiri::XML(feedbody)

feed_description = get_description(dom1)
feed_link        = get_link(dom1)
feed_title       = get_title(dom1)

# gather the lines...
lines = []
for item in (dom1.search('item')) do

  item_description = get_description(item)
  item_link        = get_link(item)
  item_pub_date    = get_publish_date(item)
  item_title       = get_title(item)

  u = URI.parse(BASE_URL).merge(item_link)

  # The time stamp is really a date, so we'll truncate the time portion.
  parsed_date = Time.parse(item_pub_date[0, 16])

  lines << {
    'description' => item_description,
    'link'        => u,
    'pubdate'     => parsed_date.strftime('%m/%d/%Y'),
    'type'        => item_title
  } 
end

puts '<html><head><title>%s</title>' % feed_title
# add CSS or JavaScript here.
puts '<style type="text/css">'
puts 'table { background-color: #efefef; }'
puts 'tr { vertical-align: top; }'
puts 'th { text-align: left; background-color: #dfdfdf; border: 1px solid #cfcfcf; }'
puts '</style>'
puts '</head>'
puts '<body><h3><a href=\"%s\">%s</a></h3>' % [ feed_link, feed_title ]
puts '<h4>%s</h4>' % feed_description
puts '<table>'
puts '<tr><th>Published</th><th>Type</th><th>Description</th></tr>'

# sort and show the lines...
lines.sort_by{ |a| a['type'] + ' ' + a['description'] }.each do |line|
  puts '<tr><td>%s</td><td><a href="%s">%s</a></td><td>%s</td></tr>' % [
    line['pubdate'],
    line['link'],
    line['type'],
    CGI.escapeHTML(line['description'])
  ]
end

puts '</table></body></html>'
