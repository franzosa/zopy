#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import re
import argparse

from collections import Counter

parser = argparse.ArgumentParser()
parser.add_argument( '-s', "--sort",        action="store_true" )
parser.add_argument( '-f', "--flatten",     action="store_true" )
parser.add_argument( '-i', "--insensitive", action="store_true" )
parser.add_argument( '-c', "--columns",     action="store_true" )
parser.add_argument( '-a', "--alphasort",   action="store_true" )
args = parser.parse_args()

def funcFormatWord( word ):
    if args.insensitive:
        word = word.lower( )
    if args.sort:
        word = "\t".join( sorted( word.split( "\t" ) ) )
    return word

counterWords = Counter()
for line in sys.stdin:
    line = line.strip( )
    if args.flatten:
        aWords = re.split( "\s+", line )
        for word in aWords:
            word = funcFormatWord( word )
            counterWords[word] += 1
    else:
        word = funcFormatWord( line )
        counterWords[word] += 1

for word in sorted( counterWords, key=lambda x: x if args.alphasort else counterWords[x] ):
    if not args.columns:
        print( "{:> 10}\t{}".format( counterWords[word], word ) )
    else:
        print( "{}\t{}".format( word, counterWords[word] ) )
