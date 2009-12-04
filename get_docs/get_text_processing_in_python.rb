#!/usr/bin/env ruby

# Get the text version of "Text Processing In Python".
# 
# Demo's creating a directory with exception handling, 
# retrieving a page from 'http://gnosis.cx/TPiP/', and saving it to disk.
# 
# Greg Ferguson - Fri Dec  4 12:31:53 2009

require 'rubygems'
require 'open-uri'
require 'uri'

BASE_URL = 'http://gnosis.cx/TPiP/'
DIRNAME  = './text_processing_in_python'

FILES = [
  'acknowledgments.txt',
  'intro.txt',
  'chap1.txt',
  'chap2.txt',
  'chap3.txt',
  'chap4.txt',
  'chap5.txt',
  'appendix_a.txt',
  'appendix_b.txt',
  'appendix_c.txt',
  'appendix_d.txt',
  'glossary.txt'
]

print 'Creating directory: %s... ' % DIRNAME
begin
  Dir.mkdir(DIRNAME)
  puts 'created.'
rescue Errno::EEXIST => e
  puts 'already exists.'
rescue => e
  puts e.to_s
  exit
end

FILES.each do |filename|
  url = BASE_URL + filename
  print 'Getting %s... ' % url
  begin
    File.open(File.join(DIRNAME, filename), 'w') do |content|

      begin
        body = open(url).read
      rescue => e
        puts e.to_s
        next
      end

      # everything is fine
      content.write(body)
      content.close()
      puts 'done.'
    end
  rescue => e
    puts 'can not read or save.'
  end
end

