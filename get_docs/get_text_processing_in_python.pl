#!/usr/bin/env perl

# Get the text version of "Text Processing In Python".
# 
# Demo's creating a directory with exception handling, 
# retrieving a page from 'http://gnosis.cx/TPiP/', and saving it to disk.
# 
# Greg Ferguson - Tue Dec  1 21:15:19 MST 2009

use File::Spec;
use LWP::Simple;
use URI;

my $BASE_URL = 'http://gnosis.cx/TPiP/';
my $DIRNAME  = './text_processing_in_python';

my @FILES = (
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
);

printf('Creating directory: %s...', $DIRNAME);
eval { mkdir($DIRNAME) };
if ($@) {
    print "created.\n";
} else {
    print "already exists.\n";
}

foreach my $filename (@FILES) {
    my $url = $BASE_URL . $filename;
    printf('Getting %s... ', $url);
    open(my $content, '>', File::Spec->catfile($DIRNAME, $filename)) or die $!; 

    my $body = get($url) or die $!;
        
    # everything is fine
    print $content $body;
    close $content;
    print "done.\n";
}

