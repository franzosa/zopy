#!/usr/bin/env python

"""
Subsets a GOA mapping with a set of UniProt identifiers
(e.g. those of UniRef90/50 centroids)
====
Author: Eric Franzosa (eric.franzosa@gmail.com)
"""

from __future__ import print_function

import os
import sys
import re
import argparse

from zopy.utils import iter_rows, say

#-------------------------------------------------------------------------------
# cli
#-------------------------------------------------------------------------------

parser = argparse.ArgumentParser( )
parser.add_argument( "goa" )
parser.add_argument( "gene_list" )
parser.add_argument( "--outfile", default="goa_parse.tsv" )
parser.add_argument( "--require-cafa-code", action="store_true" )
parser.add_argument( "--gene-prefix", default="" )
args = parser.parse_args( )

#-------------------------------------------------------------------------------
# constants
#-------------------------------------------------------------------------------

cafa_codes = {"EXP", "TAS", "IC"}

#-------------------------------------------------------------------------------
# load gene set
#-------------------------------------------------------------------------------

genes = set( )
for row in iter_rows( args.gene_list ):
    genes.add( row[0] )
say( "Loaded", len( genes ), "genes" )
    
#-------------------------------------------------------------------------------
# process goa file
#-------------------------------------------------------------------------------

"""
The GOA (.gaf) file is tab-delimited. 
Comment lines start with "!"
Col2 is the uniprot id (a superset of uniref50).
Col5 is the Gene Ontology annotation.
Col4 is a logical modifier of the uniprot->go mapping.
  Must exclude the cases where this is "NOT".
Col7 is a short evidence code
"""
    
# term->gene mapping
mapping = {}
annotated = set( )

for row in iter_rows( args.goa ):
    if row[0][0] == "!":
        continue
    gene = row[1]
    term = row[4]
    qual = row[3]
    code = row[6]
    if gene not in genes:
        continue
    if "NOT" in qual:
        continue
    if args.require_cafa_code and code not in cafa_codes:
        continue
    # all checks pass
    inner = mapping.setdefault( term, set( ) )
    inner.add( gene )
    annotated.add( gene )

say( "Using", len( mapping ), "terms" )
say( "Annotated", len( annotated ), "genes, i.e.",
     "{:.1f}%".format( 100.0 * len( annotated ) / len( genes ) ) )
    
#-------------------------------------------------------------------------------
# write output
#-------------------------------------------------------------------------------

fh = open( args.outfile, "w" )
for term in sorted( mapping ):
    genes = [args.gene_prefix + gene for gene in mapping[term]]
    genes.sort( )
    outline = [term] + genes
    print( "\t".join( outline ), file=fh )
fh.close( )
say( "Wrote mapping to:", args.outfile )
