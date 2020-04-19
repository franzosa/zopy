#!/usr/bin/env python

import os
import sys
import re
import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument( "template", help='' )
parser.add_argument( "-a", "--args", nargs="+", help='' )
parser.add_argument( "-e", "--execute", action="store_true", help='' )
parser.add_argument( "-d", "--delim", default=".", help='' )
parser.add_argument( "-s", "--delim_stop", default=0, type=int, help='' )
args = parser.parse_args()

# utility
def path2name ( path ):
    items = os.path.split( path )[1].split( args.delim )
    if len( items ) == 1:
        return items[0]
    else:
        return args.delim.join( items[0:args.delim_stop+1] )

# load template
with open( args.template ) as fh:
    slurmlines = fh.readlines()

# make substitutions
for i, arg in enumerate( args.args ):
    i = i + 1
    slurmlines = map( 
        lambda line: re.sub( "\$%d([^0-9])" % ( i ), arg+"\\1", line ),
        slurmlines,
        )
    slurmlines = map( 
        lambda line: re.sub( "%%%d([^0-9])" % ( i ), path2name( arg )+"\\1", line ),
        slurmlines,
        )

# check that everything was substituted
for line in slurmlines:
    match = re.search( r"([$%][0-9]+)", line )
    if match:
        print >>sys.stderr, match.group( 1 ), "in", line, "not completed by arguments"

# write template
commandfile = "-".join( map( path2name, args.args ) ) + ".slurm"
with open( commandfile, "w" ) as fh:
    print >>fh, "".join( slurmlines )

# execute?
if args.execute:
    os.system( "sbatch %s" % ( commandfile ) )   
    print >>sys.stderr, "submitted", commandfile
    # RC requests waiting 1 second between submissions
    time.sleep( 1 )
else:
    print >>sys.stderr, "Nothing executed; inspect slurm files for errors."
