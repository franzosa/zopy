#!/usr/bin/env python

import sys
import argparse
import csv

from zopy.utils import try_open, say
from zopy.dictation import col2dict, polymap
from zopy.enrichments import rank_enrich, c_rank_fields, Link
# common elements
import zopy.scripts.enrich_fisher as interface

#-------------------------------------------------------------------------------
# utils specific to this script
#-------------------------------------------------------------------------------

def get_args( ):
    parser = argparse.ArgumentParser( )
    parser.add_argument( "values", 
                         help="list of keys of interest and values" )
    parser.add_argument( "-m", "--min-overlap",
                         type=int,
                         help="minimum overlap between key set and given values" )
    interface.add_common_args( parser )
    args = parser.parse_args( )
    return args

#-------------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------------

def main( ):
    args = get_args( )
    # load key values
    def make_link( row ):
        key = row[1] if args.linked else row[0]
        return Link( key, float( row[-1] ) )
    values = col2dict(
        args.values,
        func=make_link,
        headers=args.skip_headers, )
    # load key sets
    key_sets = polymap(
        args.key_sets,
        reverse=args.reversed_mapping, )
    # perform analysis
    results = rank_enrich( 
        values,
        key_sets,
        depletions=not args.exclude_depletions,
        intersect_annotated=args.intersect_annotated,
        fdr=args.fdr,
        min_overlap=args.min_overlap,
        verbose=False,
    )
    # write results
    fh = open( args.outfile, "w" ) if args.outfile is not None else sys.stdout
    writer = csv.writer( fh, dialect="excel-tab" )
    writer.writerow( c_rank_fields )
    for R in results:
        writer.writerow( R.row( ) )
    # wrapup
    if len( results ) == 0:
        say( "# NO SIGNIFICANT ENRICHMENTS" )
    fh.close( )
    return None

if __name__ == "__main__":
    main( )
