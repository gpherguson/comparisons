#!/usr/bin/env ruby -w

require 'rubygems'
require 'mechanize'
require 'nokogiri'
require 'rss'

JOBS_URL   = 'http://phoenix.craigslist.org/sof/index.html'
HREF_REGEX = %r{phoenix\.craigslist\.org/evl/sof/}
JOB_REGEX  = %r/\b(?:perl|ruby|sql|python|postgres)\b/i

mech = Mechanize.new

mech.get(JOBS_URL)

content = RSS::Maker.make('2.0') do |_feed|
  _feed.channel.title       = "Craig's List jobs"
  _feed.channel.link        = JOBS_URL
  _feed.channel.description = "Software jobs of interest at Craig's List"
  _feed.items.do_sort       = true # sort items by date

  mech.page.links_with(:href => HREF_REGEX).each do |_link|

    mech.get(_link.href)
    response_body = Nokogiri::HTML(mech.page.content).inner_text

    if ( response_body[JOB_REGEX] ) 
      post_date = response_body[/Date:\s+(\S+\s+\S+\s+\S+)/i, 1]
      item = _feed.items.new_item
      item.date  = Time.parse(post_date)
      item.link  = _link.href
      item.title = mech.page.at('h2').text.squeeze(' ').strip
    end
  end
end

puts "Content-type: application/rss+xml"
puts
puts content, "\n"

