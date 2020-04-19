#!/usr/bin/env python

"""
Perform cut and reordering operations
===============================================
Author: Eric Franzosa (eric.franzosa@gmail.com)
"""

from __future__ import print_function

import os
import sys
import csv
import argparse

# constants
c_span = "-"
c_na = "#N/A"

def get_args( ):
    parser = argparse.ArgumentParser( )
    parser.add_argument( "bands", nargs="*", help="" )
    parser.add_argument( "-i", "--inspect", action="store_true", help="" )
    args = parser.parse_args( )
    return args
    
def parse_bands( bands ):
    order = []
    for band in bands:
        if band[0] == c_span:
            # -N
            stop = int( band[1:] )
            for i in range( 1, stop + 1 ):
                order.append( i )
        elif band[-1] == c_span:
            # N-
            order.append( int( band[0:-1] ) )
            order.append( c_span )
        elif c_span in band:
            # M-N
            start, stop = map( int, band.split( c_span ) )
            for i in range( start, stop + 1 ):
                order.append( i )
        else:
            # N
            order.append( int( band ) )
    # adjust order to base-0 indexing
    order = [k-1 if k != c_span else c_span for k in order]
    return order

def inspect( ):
    row = csv.reader( sys.stdin, csv.excel_tab ).next( )
    for i, item in enumerate( row ):
        print( "% 5d %s" % (i + 1, item) )
    return None

def rewrite( order ):
    writer = csv.writer( sys.stdout, csv.excel_tab )
    for row in csv.reader( sys.stdin, csv.excel_tab ):
        row2 = []
        for i, pos in enumerate( order ):
            if pos == c_span:
                row2 += row[1+order[i-1]:]
            else:
                try:
                    row2.append( row[pos] )
                except:
                    row2.append( c_na )
        writer.writerow( row2 )
    return None

def main( ):
    args = get_args( )
    if args.inspect:
        inspect( )
    else:
        rewrite( parse_bands( args.bands ) )

if __name__ == "__main__":
    main( )
