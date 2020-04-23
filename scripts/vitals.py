#!/usr/bin/env python

import sys
import argparse
from math import floor

from numpy import mean, std
from scipy.stats.mstats import mquantiles

from zopy.utils import reader, warn, die
from zopy.table2 import nesteddict2table
# changed after git reorg
from scripts.excel import excel

c_eps = 1e-20
c_props = "N Sum #0s %0s Min Q1 Q2_Med Q3 Max Mean StDev CfVar".split( )

def get_args( ):
    parser = argparse.ArgumentParser( )
    parser.add_argument( "-g", "--engin",
                         action="store_true", help="Use engineering notation" )
    parser.add_argument( "-s", "--stratified",
                         action="store_true", help="Stratify by first entry" )
    parser.add_argument( "-e", "--excel",
                         action="store_true", help="Excel-print results" )
    parser.add_argument( "-t", "--transpose",
                         action="store_true", help="Transpose the results" )
    args = parser.parse_args( )
    return args
    
def read_stream( stream, stratified=False ):
    total, bad = 0, 0
    data = {}
    for row in reader( stream ):
        if not stratified:
            key, values = "#", row
        else:
            key, values = row[0], row[1:]
        total += len( values )
        values2 = []
        for v in values:
            try:
                values2.append( float( v ) )
            except:
                warn( "bad value:", v )
                bad += 1
        inner = data.setdefault( key, [] )
        inner += values2
    if bad > 0:
        warn( "bad values: %d (%.2f%%)" % ( bad, 100 * bad / float( total ) ) )
    data = {k:v for k, v in data.items( ) if len( v ) > 0}
    return data
        
def engin_style( number ):
    pairs = [
        [1e12, "T"],
        [1e9,  "B"],
        [1e6,  "M"],
        [1e3,  "K"],
        ]
    sign = 1 if number >= 0 else -1
    number = abs( number )
    for v, c in pairs:
        if number > v:
            front = sign * int( number / v )
            number = str( front ) + c
            break
    else:
        number = sign * number
    return str( number )

def pretty( number, engin=False ):
    intish = False
    if abs( number - int( number ) ) <= c_eps:
        number = int( number )
        intish = True
    if abs( number ) > 1e4 and engin:
        number = engin_style( number )
    elif abs( number ) > 1e2 and not intish:
        number = round( number, 1 )
    elif abs( number ) > 1e-3 and not intish:
        number = "%.3f" % ( number )
    elif not intish:
        number = "%.3e" % ( number )
    return str( number )

def row_stats( row, as_strings=True, engin=False ):  
    q1, q2, q3 = mquantiles( row )
    stats = {}
    stats["N"] = len( row )
    stats["#0s"] = len( [k for k in row if abs( k ) < c_eps] )
    stats["%0s"] = stats["#0s"] / float( len( row ) )
    stats["Sum"] = sum( row )
    stats["Min"] = min( row )
    stats["Q1"] = q1
    stats["Q2_Med"] = q2
    stats["Q3"] = q3
    stats["Max"] = max( row )
    stats["Mean"] = mean( row )
    stats["StDev"] = std( row )
    stats["CfVar"] = stats["StDev"] / stats["Mean"] if stats["Mean"] != 0 else 0
    if set( stats.keys( ) ) != set( c_props ):
        die( "Inconsistent stat lists. Check code." )
    if as_strings:
        stats = {k:pretty( v, engin ) for k, v in stats.items()}
    return stats 

def main( ):
    args = get_args( )
    data = read_stream( sys.stdin, stratified=args.stratified )
    for stratum in sorted( data ):
        data[stratum] = row_stats( data[stratum], engin=args.engin )
    tdata = nesteddict2table( data, aColheads=c_props, origin="STAT \ LEVEL" )
    # counter intuitive, but "transposed" is opposite expectation here
    if not args.transpose:
        tdata.transpose( )
    if args.excel:
        excel( tdata.data )
    else:
        tdata.dump( )

if __name__ == "__main__":
    main( )
