#!/usr/bin/env perl

# Code to read Guitar Center's used equipment feed, parse the article titles,
# and print them as a HTML page.

use CGI;
use HTTP::Date;
use LWP::Simple qw($ua get);
use URI;
use XML::LibXML;

my $BASE_URL         = 'http://used.guitarcenter.com/usedGear/';
my $FEED_URL         = 'usedListings_rss.xml';
my $URL_OPEN_TIMEOUT = 10;

my $CSS = <<EOT;
    table {
        background-color: #efefef;
    }
    tr {
        vertical-align: top;
    }
    th {
        text-align: left;
        background-color: #dfdfdf;
        border: 1px solid #cfcfcf;
    }
EOT

# get the title for the element.
sub get_title {
    my $_item = shift;
    return ( ( $_item->getElementsByTagName('title') )[0]->childNodes )[0]
        ->nodeValue;
}

# get the description for the element.
sub get_description {
    my $_item = shift;
    return ( ( $_item->getElementsByTagName('description') )[0]->childNodes )
        [0]->nodeValue;
}

# get the link for the element.
sub get_link {
    my $_item = shift;
    return ( ( $_item->getElementsByTagName('link') )[0]->childNodes )[0]
        ->nodeValue;
}

# get the publish date for the element.
sub get_publish_date {
    my $_item = shift;
    return ( ( $_item->getElementsByTagName('pubDate') )[0]->childNodes )[0]
        ->nodeValue;
}

my $cgi = new CGI;

my $feedbody;
$ua->timeout($URL_OPEN_TIMEOUT);
eval { $feedbody = get( $BASE_URL . $FEED_URL ) };
if ($@) {
    print STDERR $@, "\n";
    exit 0;
}

my $dom1 = XML::LibXML->load_xml( 'string' => $feedbody );

my $feed_description = get_description($dom1);
my $feed_link        = get_link($dom1);
my $feed_title       = get_title($dom1);

# gather the lines...
my @lines = ();
foreach my $item ( $dom1->getElementsByTagName('item') ) {
    my $item_description = get_description($item);
    my $item_link        = get_link($item);
    my $item_pub_date    = get_publish_date($item);
    my $item_title       = get_title($item);

    my $u = URI->new_abs( $item_link, $BASE_URL );

    # The time stamp is really a date, so we'll truncate the time portion.
    my $parsed_date = str2time( substr( $item_pub_date, 0, 16 ) );
    my ( $mday, $mon, $year ) = ( localtime($parsed_date) )[ 3 .. 5 ];

    push(
        @lines,
        {   'description' => $item_description,
            'link'        => $u,
            'pubdate' =>
                sprintf( '%02d/%02d/%04d', 1 + $mon, $mday, 1900 + $year ),
            'type' => $item_title
        }
    );
}

# sort the lines...
my @sorted_lines = sort {
    "$a->{'type'} $a->{'description'}" cmp "$b->{'type'} $b->{'description'}"
} @lines;

print $cgi->start_html(
    -title => $feed_title,
    -style => { -code => $CSS }
    ),
    $cgi->h3( $cgi->a( { -href => $feed_link }, $feed_title ) ),
    $cgi->h4($feed_description),
    $cgi->table(
        $cgi->Tr( $cgi->th([ 'Published', 'Type', 'Description' ]) ),
        join(
            "\n",
            map {
                $cgi->Tr(
                    $cgi->td( $_->{'pubdate'} ),
                    $cgi->td(
                        $cgi->a( { -href => $_->{'link'} }, $_->{'type'} )
                    ),
                    $cgi->td( $cgi->escapeHTML( $_->{'description'} ) )
                    )
                } @sorted_lines
        )
    ),
    $cgi->end_html,
    "\n";
