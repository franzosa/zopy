#!/usr/bin/env python

import sys
import argparse
import csv

from zopy.utils import try_open, say, die
from zopy.dictation import col2dict, polymap
from zopy.enrichments import fisher_enrich, c_fisher_fields

#-------------------------------------------------------------------------------
# utils shared with enrich_rank
#-------------------------------------------------------------------------------
    
def add_common_args( parser ):
    """ shared between fisher and rank """
    parser.add_argument( "gene_sets", 
                         help="mapping of gene set names to genes", )
    parser.add_argument( "-H", "--skip-headers", 
                         action="store_true", 
                         help="Gene list/values files have headers", )
    parser.add_argument( "-d", "--exclude-depletions", 
                         action="store_true", 
                         help="Focus on enrichments only (depletions excluded from output)", )
    parser.add_argument( "-A", "--intersect-annotated",
                         action="store_true", 
                         help="Ignore genes that aren't annotated at all", )
    parser.add_argument( "-f", "--fdr",
                         type=float,
                         help="Focus on fdr significant results (provide threshold)", )
    parser.add_argument( "-r", "--reversed-mapping", 
                         action="store_true",
                         help="Mapping file is reversed (feature->set)", )
    parser.add_argument( "-l", "--linked", 
                         action="store_true",
                         help="Gene lists include an extra column to link to set definitions" )
    parser.add_argument( "-o", "--outfile",
                         default=None,
                         help="Where to put the output" )
    return None

#-------------------------------------------------------------------------------
# utils specific to this script
#-------------------------------------------------------------------------------

def get_args( ):
    parser = argparse.ArgumentParser( )
    parser.add_argument( "genes", 
                         help="list of genes of interest" )
    parser.add_argument( "-m", "--min-expected-overlap",
                         type=int,
                         help="minimum number of items in expected overlap class" )
    parser.add_argument( "-b", "--background",
                         default=None,
                         help="list of genes to consider as background", )
    parser.add_argument( "-B", "--intersect-background", 
                         action="store_true", 
                         help="Ignore genes that aren't in the background", )
    add_common_args( parser )
    args = parser.parse_args( )
    return args
    
#-------------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------------

def main( ):
    args = get_args( )
    # load genes (accounting for linkage)
    genes = col2dict(
        args.genes,
        value=(1 if args.linked else None),
        headers=args.skip_headers, )
    genes = {g:(g if k is None else k) for g, k in genes.items( )}
    # load background (accounting for linkage)
    background = None
    if args.background is not None:
        background = col2dict(
            args.background,
            value=(1 if args.linked else None),
            headers=args.skip_headers, )
        background = {g:(g if k is None else k) for g, k in background.items( )}
    # load gene sets
    gene_sets = polymap(
        args.gene_sets,
        reverse=args.reversed_mapping, )
    # run analysis
    results = fisher_enrich( 
        genes,
        gene_sets,
        depletions=not args.exclude_depletions,
        background=background,
        intersect_background=args.intersect_background,
        intersect_annotated=args.intersect_annotated,
        fdr=args.fdr,
        min_expected_overlap=args.min_expected_overlap,
        verbose=False,
    )
    # write results
    fh = open( args.outfile, "w" ) if args.outfile is not None else sys.stdout
    writer = csv.writer( fh, dialect="excel-tab" )
    writer.writerow( c_fisher_fields )
    for R in results:
        writer.writerow( R.row( ) )
    # wrapup
    if len( results ) == 0:
        say( "# NO SIGNIFICANT ENRICHMENTS" )
    fh.close( )
    return None

if __name__ == "__main__":
    main( )
