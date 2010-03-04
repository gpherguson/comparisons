#!/usr/bin/env ruby -w

require 'rubygems'
require 'mechanize'
require 'nokogiri'
require 'uri'
require 'rss'
require 'set'

JOBS_URL    = 'http://phoenix.craigslist.org/sof/index.html'
HREF_SUBSTR = %r{phoenix\.craigslist\.org/evl/sof/}
JOB_KEYWORDS = %w[ perl ruby sql python postgres ]

mech = Mechanize.new

mech.get(JOBS_URL)

content = RSS::Maker.make('2.0') do |_feed|
  _feed.channel.title       = "Craig's List jobs"
  _feed.channel.link        = JOBS_URL
  _feed.channel.description = "Software jobs of interest at Craig's List"
  _feed.items.do_sort       = true # sort items by date

  mech.page.links_with(:href => HREF_SUBSTR).each do |_link|

    mech.get(_link.href)
    response_body = Nokogiri::HTML(mech.page.content).inner_text

    hits = response_body.split(' ').select{ |w| JOB_KEYWORDS.include?(w.downcase) }.to_set
    if (hits.any?)
      post_date = response_body[/Date:\s+(\S+\s+\S+\s+\S+)/i, 1]
      i = _feed.items.new_item
      i.date        = Time.parse(post_date)
      i.link        = _link.href
      i.title       = mech.page.at('h2').text.squeeze(' ').strip
      i.description = 'Matching words: ' << hits.to_a.join(', ')
    end
  end
end

puts "Content-type: application/rss+xml"
puts
puts content, "\n"
