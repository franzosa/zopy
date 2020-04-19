#!/usr/bin/env python

"""
Align tabular data on the command line
-----------------------------------------------
Author: Eric Franzosa (eric.franzosa@gmail.com)
"""

from __future__ import print_function

import os
import sys
import argparse
import csv

from zopy.utils import try_open

def get_args( ):
    parser = argparse.ArgumentParser()
    parser.add_argument( "stream",
                         nargs="?", default=None )
    parser.add_argument( "-t", "--trim",
                         action="store_true" )
    parser.add_argument( "-n", "--norm",
                         action="store_true" )
    parser.add_argument( "-r", "--align-right",
                         action="store_true" )
    parser.add_argument( "-i", "--itunes",
                         action="store_true" )
    parser.add_argument( "-l", "--limit",
                         type=int, default=30 )
    return parser.parse_args( )

def puncture( s, l, fill="[...]" ):
    l2 = int( l / 2.0 )
    return s[0:l2] + fill + s[-l2:]
    
def excel( data, trim=False, limit=None, norm=False,
           itunes=False, align_right=False ):

    maxlens = []
    for r, row in enumerate( data ):
        if len( maxlens ) == 0:
            maxlens = [0 for s in row]
        for c, s in enumerate( row ):
            if trim:
                if limit is not None and len( s ) > limit:
                    s = puncture( s, limit )
                    row[c] = s
            maxlens[c] = max( maxlens[c], len( s ) )
    if norm:
        x = max( maxlens )
        maxlens = [x] * len( maxlens )

    switch = False
    for row in data:
        switch = not switch
        spacer = " "
        if switch and itunes:
            spacer = "."
        for c, s in enumerate( row ):
            padding = spacer * (maxlens[c] - len( s ))  
            if align_right:
                print( spacer + padding + s, end=" " )
            else:
                print( s + padding + spacer, end=" " )
        print( )

def main( ):
    args = get_args( )
    stream = sys.stdin
    if args.stream is not None:
        stream = try_open( args.stream )
    data = [row for row in csv.reader( stream, csv.excel_tab )]
    excel( data,
           trim=args.trim,
           limit=args.limit,
           norm=args.norm,
           align_right=args.align_right,
           itunes=args.itunes,
           )

if __name__ == "__main__":
    main( )
