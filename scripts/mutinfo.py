#! /usr/bin/env python

import os, sys, re, glob, argparse
import csv
from zopy.stats import mutinfo, shannon

parser = argparse.ArgumentParser()
#parser.add_argument( '-1', "--col1", type=int, default=0 )
parser.add_argument( '-m', "--missing", help="exclude missing values" )
args = parser.parse_args()

total = 0
bad = 0
aX = []
aY = []
for aItems in csv.reader( sys.stdin, delimiter="\t", quotechar="", quoting=csv.QUOTE_NONE ):
    total += 1
    if len( aItems ) != 2:
       bad += 1
       print >>sys.stderr, "ignoring", "\t".join( aItems )
    else:
        aX.append( aItems[0] )
        aY.append( aItems[1] )

# determine sensible pairs
aX2 = []
aY2 = []
for x, y in zip( aX, aY ):
    if not args.missing or ( x != "" and y != "" ):
        aX2.append( x )
        aY2.append( y )
    else:
        print >>sys.stderr, "ignoring", x, y
        bad += 1
aX, aY = aX2, aY2

# output
print "total pairs  :", total
print "bad pairs    :", bad, "( %.1f%% )" % ( 100 * bad / float( total ) )
print "col1 entropy :", shannon( aX )
print "col2 entropy :", shannon( aY )
print "mutual info  :", mutinfo( aX, aY )
print "normalized   :", mutinfo( aX, aY, normalized=True )
