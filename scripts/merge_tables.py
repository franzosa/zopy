#!/usr/bin/env python

import os
import sys
import re
import glob
import argparse

from zopy.table2 import table, c_strNA, nesteddict2table
from zopy.utils import warn

# ---------------------------------------------------------------
# argparse 
# ---------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument( 
    "tables",
    nargs="+",
    help="one or more data tables",
)
parser.add_argument( 
    "-e", "--fill-empty", 
    default=None, 
    help="value to insert in place of missing values",
)
parser.add_argument( 
    "-m", "--metatable", 
    default=None,
    help="additional metadata table to attach",
)
parser.add_argument( 
    "-l", "--legacy",
    action="store_true",
    help="iteratively merge tables (better maintains feature order)",
)
args = parser.parse_args()

# ---------------------------------------------------------------
# load and process data
# ---------------------------------------------------------------

p = args.tables[0]

if len( args.tables ) == 1:
    t = table( p )
elif args.legacy:
    t = table( p )
    for p2 in args.tables[1:]:
        t2 = table( p2 )
        t.merge( t2 )
else:    
    data = {}
    for p in args.tables:
        d = table( p ).table2nesteddict( )
        for r in d:
            inner = data.setdefault( r, {} )
            for c in d[r]:
                if c in inner and inner[c] != d[r][c]:
                    warn( p, "overwrites", r, c, inner[c], "with", d[r][c] )
                inner[c] = d[r][c]
    t = nesteddict2table( data, empty=c_strNA )

if args.metatable is not None:
    t.metamerge( table( args.metatable ) )
if args.fill_empty is not None:
    t.apply_entries( lambda x: x if x != c_strNA else args.fill_empty )
    
# ---------------------------------------------------------------
# dump table
# ---------------------------------------------------------------

t.dump( )
