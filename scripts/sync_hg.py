#!/usr/bin/env python

import os
import sys
import argparse
from collections import Counter

from zopy.utils import qw

c_defaults = qw( """
py
R
sh
md
slurm
slurm-template
""" )

# argument parsing (python argparse)
parser = argparse.ArgumentParser()
parser.add_argument( "start", default="." )
parser.add_argument( "--extensions", nargs="+", default=None )
parser.add_argument( "--no-defaults", action="store_true" )
parser.add_argument( "--execute", action="store_true" )
args = parser.parse_args()

# setup extensions
extensions = [] if args.extensions is None else args.extensions
if not args.no_defaults:
    extensions += c_defaults
print >>sys.stderr, "Targeting these extensions:", extensions

# find paths
C = Counter( )
pxpairs = []
for dirpath, dirname, filenames in os.walk( args.start ):
    for f in filenames:
        x = "n/a"
        if "." in f:
            x = os.path.split( f )[1].split( "." )[-1]
        p = os.path.join( dirpath, f )
        pxpairs.append( [p, x] )
        C[x] += 1

# action    
if args.execute:
    for p, x in pxpairs:
        if x in extensions:
            print >>sys.stderr, "committing:", p
            os.system( "hg add {}".format( p ) )
else:
    for x in sorted( C, key=lambda xi: C[xi] ):
        print x, C[x]
