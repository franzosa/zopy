#!/usr/bin/env python

import os
import sys
import argparse

from numpy import median
from scipy.stats.mstats import mquantiles
import scipy.spatial.distance as spd

from zopy.table2 import table, nesteddict2table
from zopy.utils import warn

def get_args( ):
    parser = argparse.ArgumentParser()
    parser.add_argument( "table", help="" )
    parser.add_argument( "-l", "--last-metadata", help="" )
    parser.add_argument( "-s", "--stratify-by", help="" )
    args = parser.parse_args( )
    return args

def check( t ):
    failed = {}
    t.float( )
    # place samples on rows
    t.transpose( )
    for s, row in t.iter_rows( ):
        if sum( row ) == 0:
            failed[s] = "Sample with zero sum"
    t.delete( "headers", failed )
    array = t.table2array( )
    dists = spd.squareform( spd.pdist( array, "braycurtis" ) )
    median_dists = []
    indices = set( range( len( t.rowheads ) ) )
    for i, s in enumerate( t.rowheads ):
        others = list( indices - {i} )
        median_dists.append( median( dists[i][others] ) )
    q1, q2, q3 = mquantiles( median_dists )
    limit = q3 + 1.5 * (q3 - q1)
    qmin = min( median_dists )
    qmax = max( median_dists )
    summary = "Comparison summary: N=%d min=%.3f q1=%.3f q2=%.3f q3=%.3f uif=%.3f max=%.3f" % (
        len( t.rowheads ), qmin, q1, q2, q3, limit, qmax ) 
    if limit > 1:
        warn( "Upper inner fence exceeds theoretical limit: %.3f > %.3f" %
              ( limit, 1.0 ) )    
    for m, s in zip( median_dists, t.rowheads ):
        if m > limit:
            failed[s] = "Extreme distance: {}".format( m )
    return summary, failed
    
def main( ):
    args = get_args( )
    t = table( args.table, verbose=False )
    if args.stratify_by is None:
        dt = {}
        dt["ALL_SAMPLES"] = t
    else:
        dt = t.stratify( args.stratify_by )
    reports = {}
    for level, t in dt.items( ):
        if args.last_metadata is not None:
            m, t = t.metasplit( args.last_metadata )
        reports[level] = check( t )
    for level, [summary, failed] in reports.items( ):
        print "Considering table <{}> at level <{}>:".format( args.table, level )
        print "  Summary:", summary
        print "  FAILED: ", len( failed )        
        for s, msg in failed.items( ):
            print "\t".join( ["  FAILED:", s, msg] )
    return None
        
if __name__ == "__main__":
    main( )
