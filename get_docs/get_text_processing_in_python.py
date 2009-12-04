#!/usr/bin/env python

"""
Get the text version of "Text Processing In Python".

Demo's creating a directory with exception handling, 
retrieving a page from 'http://gnosis.cx/TPiP/', and saving it to disk.

Greg Ferguson - Tue Dec  1 21:15:19 MST 2009
"""

import urllib2
import os

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

print 'Creating directory: {0}...'.format(DIRNAME),
try:
    os.mkdir(DIRNAME)
    print 'created.'
except:
    print 'already exists.'

for filename in (FILES):
    url = BASE_URL + filename
    print 'Getting {0}...'.format(url),
    try:
        content = open(os.path.join(DIRNAME, filename), 'w')

        req = urllib2.Request(url)
        try:
            body = urllib2.urlopen(req).read()
        except IOError, e:
            if hasattr(e, 'reason'):
                print 'Cannot reach {0}'.format(url)
                print 'Reason:', e.reason
            elif hasattr(e, 'code'):
                print 'Connection failed.'
                print 'Error code:', e.code
        
        # everything is fine
        content.write(body)
        content.close()
        print 'done.'

    except:
        print 'can not read or save.'
