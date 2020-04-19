#!/usr/bin/env python

"""
Grep on a specific column
===============================================
Author: Eric Franzosa (eric.franzosa@gmail.com)
"""

import os
import sys
import re
import csv
import argparse

def get_args( ):
    parser = argparse.ArgumentParser( )
    parser.add_argument( "pattern", help="" )
    parser.add_argument( "-e", "--exact", action="store_true", help="" )
    parser.add_argument( "-c", "--column", type=int, help="" )
    parser.add_argument( "-v", "--invert", action="store_true", help="" )
    args = parser.parse_args( )
    return args

def main( ):
    args = get_args( )   
    writer = csv.writer( sys.stdout, csv.excel_tab )
    for row in csv.reader( sys.stdin, csv.excel_tab ):
        include = False
        for i, field in enumerate( row ):
            if args.column is None or i+1 == args.column:
                if args.exact:
                    match = args.pattern == field
                else:
                    match = re.search( args.pattern, field )
                if match or (args.invert and not match):
                    include = True
                    break
        if include:
            writer.writerow( row )

if __name__ == "__main__":
    main( )
