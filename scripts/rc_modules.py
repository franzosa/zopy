#! /usr/bin/env python

import os, sys, re, glob, argparse
import urllib2

local = "/dev/shm/modules.tmp"
url = "https://rc.fas.harvard.edu/resources/module-list/"

if not os.path.exists( local ):
    print >>sys.stderr, "Downloading module list from the web to /dev/shm/..."
    with open( local, "w" ) as fh:
        opener = urllib2.build_opener()
        opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        webfile = opener.open( url )
        fh.writelines( webfile.readlines() )

hits = []
with open( local ) as fh:
    for line in fh:
        if "module_name" in line:
            match = re.search( '>([^"]*?)</a>', line )
            if match:
                name = match.group( 1 ).replace( "&#47;", "/" )
                date = None
                match = re.search( 'updated: (\d+/\d+/\d+)', line )
                if match:
                    date = match.group( 1 )
                    date = map( int, date.split( "/" ) )
                    date = [date[2], date[0], date[1]]
                else:
                    date = [0, 0, 0]
                good = True
                for pattern in sys.argv[1:]:
                    if pattern not in name:
                        good = False
                if good:
                    hits.append( [date, name] )

counter = 0
mods = []
for date, name in sorted( hits, reverse=True ):
    counter += 1
    mods.append( name )
    print "% 3d. %04d-%02d-%02d %s" % tuple( [counter] + date + [name] )

if len( mods ) > 0:
    choice = input( "Selection?: " )
    os.system( "module load {}".format( mods[choice-1] ) )
else:
    print "Sorry, nothing found."
