#!/usr/bin/env python

import sys
import csv
import argparse

def get_args( ):
    parser = argparse.ArgumentParser( )
    parser.add_argument(
        "-c", "--column",
        type=int,     
        default=1,
        help="Focal 1-based column [Default=1]",
    )
    parser.add_argument(
        "-l", "--lower-limit", 
        default=None,
        type=float, 
        help="Lower limit [Default=None]",
    )
    parser.add_argument(
        "-u", "--upper-limit", 
        default=None, 
        type=float, 
        help="Upper limit [Default=None]",
    )
    parser.add_argument(
        "-n", "--numeric-only",
        action="store_true",
        help="Don't print non-numeric rows [Default=off]",
    )
    args = parser.parse_args( )
    return args

def main( ):
    args = get_args( )
    writer = csv.writer( sys.stdout, dialect="excel-tab" )
    for row in csv.reader( sys.stdin, dialect="excel-tab" ):
        try:
            value = float( row[args.column - 1] )
            include = True
            if args.lower_limit is not None and ( value < args.lower_limit ):
                include = False
            if args.upper_limit is not None and ( value > args.upper_limit ):
                include = False
            if include:
                writer.writerow( row )
        except:
            if not args.numeric_only:
                print writer.writerow( row )

if __name__ == "__main__":
    main( )
