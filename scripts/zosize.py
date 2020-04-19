#!/usr/bin/env python

import os
import sys
import subprocess

from numpy import mean

from zopy.table2 import nesteddict2table

sizes = {}
command = "ls -l " + " ".join( sys.argv[1:] )
cmd = subprocess.Popen( command, shell=True, stdout=subprocess.PIPE )
for line in cmd.stdout:
    items = line.split( )
    if len( items ) >= 8:
        size = int( items[4] )
        items = os.path.split( items[8] )[1].split( "." )
        group = "--"
        if len( items ) > 1:
            group = "." + ".".join( items[1:] )
        sizes.setdefault( "[ALL]", [] ).append( size )
        sizes.setdefault( group, [] ).append( size )
    else:
        print >>sys.stderr, "Bad line:", line

def prettysize( size ):
    for val, txt in zip( [12, 9, 6, 3, 0], "TGMKB" ):
        if size / 10**val > 1:
            return "%.1f%s" % ( round( size / 10**val, 1 ), txt )

data = {}
for group, values in sizes.items( ):
    inner = data.setdefault( group, {} )
    inner["count"] = len( values )
    inner["total"] = prettysize( sum( values ) )
    inner["mean"] = prettysize( mean( values ) )
T = nesteddict2table( data )
T.data[0][0] = "#"
T.dump( )
