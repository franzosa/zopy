#! /usr/bin/env python

import sys, os, argparse

# arguments
parser = argparse.ArgumentParser()
parser.add_argument( '--map', help="two columns: old ID -> new ID" )
parser.add_argument( '--inputs', nargs="+",  help="list of files to rename ( potentially )" )
parser.add_argument( '--execute', action="store_true", help="do the renaming" )
args = parser.parse_args()

# process map
idmap = {}
isnewid = {}
with open( args.map ) as fh:
    for line in fh:
        oldid, newid = line.strip().split( "\t" )
        if newid in isnewid:
            sys.exit( "ERROR: %s listed 2+ times in map" % ( newid ) )
        else:
            idmap[oldid] = newid
            isnewid[newid] = 1

#execute
for oldname in args.inputs:
    oldid = oldname.split( "." )[0]
    extension = ".".join( oldname.split( "." )[1:] )
    if oldid in idmap:
        newname = ".".join( [idmap[oldid], extension] )
        print >>sys.stderr, oldname, "-->", newname
        if args.execute:
            if os.path.exists( newname ):
                print >>sys.stderr, "skipped overwrite"
            else:
                os.rename( oldname, newname )
                print >>sys.stderr, "renamed!"
