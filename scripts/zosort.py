#!/usr/bin/env python

import os
import sys
import re
import argparse
import csv

from zopy.utils import tprint

def get_args( ):
    # argument parsing (python argparse)
    parser = argparse.ArgumentParser( )
    parser.add_argument( "-c", "--column",
                         type=int,
                         default=1,
                         help="" )
    parser.add_argument( "-r", "--reverse",
                         action="store_true",
                         help="" )
    parser.add_argument( "-x", "--exclude-non-numeric",
                         action="store_true",
                         help="" )
    args = parser.parse_args( )   
    return args
    
def main( ):
    args = get_args( )
    pairs = []
    for row in csv.reader( sys.stdin, csv.excel_tab ):
        try:
            rank = float( row[args.column - 1] )
        except:
            rank = None
        pairs.append( [rank, row] )
    for rank, row in sorted( pairs, reverse=args.reverse ):
        if rank is not None or not args.exclude_non_numeric:
            print "\t".join( row )

if __name__ == "__main__":
    main( )
