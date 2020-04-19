#! /usr/bin/env python

import os, sys, re, glob, argparse
from math import floor, log

if len( sys.argv ) > 1:
    base = int( sys.argv[1] )
else:
    base = 10

dictLogCounts = { 0:0, "NA":0 }
convert = { 0:0, "NA":-1 }

for line in sys.stdin:
    try:
        n = float( line.strip() )
        if n == 0:
            dictLogCounts[0] += 1
        else:
            n = floor( log( n, base ) )
            n2 = n
            n = "%d^%s%d" % ( base, "+" if n >= 0 else "", n )
            if n not in dictLogCounts:
                dictLogCounts[n] = 0
                convert[n] = base**n2
            dictLogCounts[n] += 1
    except:
        dictLogCounts["NA"] += 1

total = sum( dictLogCounts.values() )
print " CUME   OMAG            :--------: 20%"
cume = 0
for logbin in sorted( dictLogCounts.keys(), key=lambda x: convert[x] ):
    if logbin != "NA":
        value = dictLogCounts[logbin] / float( total )
        cume += value
        print "%.4f" % ( cume ), "%.4f" % ( value ), ":", logbin, "\t", "|" * int( 50 * value )
value = dictLogCounts["NA"] / float( total )
cume += value
print "%.4f" % ( cume ), "%.4f" % ( value ), ":", "NA", "\t", "|" * int( 50 * value )
print "total=", total
