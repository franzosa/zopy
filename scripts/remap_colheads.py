#! /usr/bin/env python

import sys, os, argparse
from zopy.table2 import table

# arguments
parser = argparse.ArgumentParser()
parser.add_argument( 'table', help="table with weird colheads" )
parser.add_argument( 'map', help="mapping file" )
parser.add_argument( '--split', default=".", help="string to split original colhead on" )
parser.add_argument( '--pos', default=0, type=int, help="position post splitting to isolate" )
args = parser.parse_args()

# process map
idmap, isnewid = {}, {}
with open( args.map ) as fh:
    for line in fh:
        oldid, newid = line.strip().split( "\t" )
        if newid in isnewid:
            sys.exit( "ERROR: %s listed 2+ times in map" % ( newid ) )
        else:
            idmap[oldid] = newid
            isnewid[newid] = 1

# execute
def applier ( colhead ):
    oldid = colhead.split( args.split )[args.pos]
    if oldid in idmap:
        return idmap[oldid]
    else:
        print >>sys.stderr, "can't convert", colhead, "->", oldid
        return oldid
t = table( args.table )
t.apply_colheads( applier )
t.dump()
