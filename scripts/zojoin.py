#! /usr/bin/env python

from __future__ import print_function

import os
import sys
import argparse
import csv
from collections import Counter

from zopy.utils import try_open, warn, die

# constants
c_sep = "\t"
c_na = "#N/A"

# argument parsing (python argparse)
parser = argparse.ArgumentParser()
parser.add_argument( "file1", 
                     help="file to join to (streamed); use '-' for stdin" )
parser.add_argument( "file2", 
                     help="file to join from (loaded in its entirety)" )
parser.add_argument( "--key1", 
                     default=1, 
                     type=int, 
                     help="base-1 column for file1 key" )
parser.add_argument( "--key2", 
                     default=1, 
                     type=int, 
                     help="base-1 column for file2 key" )
parser.add_argument( "--head1",
                     action="store_true",
                     help="file 1 has headers" )
parser.add_argument( "--head2",
                     action="store_true",
                     help="file 2 has headers" )
parser.add_argument( "--skip", 
                     action="store_true", 
                     help="skip file1 lines that did not match" )
parser.add_argument( "--remainder", 
                     action="store_true", 
                     help="print file2 lines that did not match" )
parser.add_argument( "--het", 
                     action="store_true", 
                     help="allow file 2 lines to have unequal lengths" )
args = parser.parse_args()

# adjust to base-0 indexing for python
args.key1 -= 1
args.key2 -= 1

# load second file to dictionary
lengths2 = []
d = {}
headers2 = None
with try_open( args.file2 ) as fh:
    for items in csv.reader( fh, dialect="excel-tab" ):
        lengths2.append( len( items ) )
        if headers2 is None and args.head2:
            headers2 = c_sep.join( items )
            continue
        key = items[args.key2]
        d.setdefault( key, {} )["\t".join( items )] = 1
print( "finished loading file2", file=sys.stderr )

# make dummy line to add when join fails
if len( set( lengths2 ) ) != 1:
    warn( "file2 lines have unequal lengths" )
    if args.het:
        dummyline2 = c_na
    else:
        die( )
else:
    dummyline2 = "\t".join( c_na for k in range( lengths2[0] ) )
if not args.head2:
    headers2 = dummyline2

# load first file, print join
counts = Counter()
lengths1 = []
hits = {}
headers1 = None
with (try_open( args.file1 ) if args.file1 != "-" else sys.stdin) as fh:
    for items in csv.reader( fh, dialect="excel-tab" ):
        line = "\t".join( items )
        lengths1.append( len( items ) )
        if headers1 is None and args.head1:
            headers1 = line
            print( "\t".join( [headers1, headers2] ) )
            continue
        key = items[args.key1]
        if key in d:
            hits[key] = 1
            counts[len( d[key] )] += 1
            for joinline in d[key]:
                print( c_sep.join( [line, joinline] ) )
        else:
            counts[0] += 1
            if not args.skip:
                print( c_sep.join( [line, dummyline2] ) )

if args.remainder:
    if len( set( lengths1 ) ) != 1:
        sys.exit( "file1 lines have unequal lengths" )
    dummyline1 = "\t".join( [c_na for k in range( lengths1[0] )] )
    for key in d:
        if key not in hits:
            for line in d[key]:
                print( "\t".join( [dummyline1, line] ) )

# report 
print( """
Summary
=======
N\t#\t%""", file=sys.stderr )
total = sum( counts.values() )
for k in sorted( counts.keys() ):
    print( "\t".join( map( str, [k, counts[k], 100 * counts[k] / float( total )] ) ), file=sys.stderr )
