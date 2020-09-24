#!/usr/bin/env python

"""
Merge 1-sample profiles into a multi-sample table
"""

import os
import sys
import re
import glob
import argparse

from zopy.utils import reader, path2name, say
from zopy.table2 import nesteddict2table

# ---------------------------------------------------------------
# argparse 
# ---------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument( 
    "inputs", 
    nargs="*",
    default=[],
    help="input files",
    )
parser.add_argument( 
    "-o", "--output",
    default=None,
    help="output file",
    )
parser.add_argument( 
    "-k", "--key-col",
    default=0,
    help="key column",
    )
parser.add_argument( 
    "-v", "--val-col",
    default=1,
    help="value column",
    )
parser.add_argument( 
    "-p", "--key-pattern",
    default=None,
    help="pattern key ( rowhead ) must match, e.g. 'M[0-9]+:' for KEGG modules",
    )
parser.add_argument( 
    "-n", "--fill-empty",
    default=None,
    help="value to insert in place of missing values",
    )
parser.add_argument( 
    "-u", "--use-headers",  
    action="store_true", 
    help="use file headers as colheads and not file names",
    )
parser.add_argument( 
    "-r", "--strip-headers",  
    action="store_true", 
    help="remove this file type's headers",
    )
parser.add_argument( 
    "-c", "--strip-comments", 
    action="store_true", 
    help="strip comments from the file ( lines beginning with # )",
    )
parser.add_argument( 
    "-f", "--file",
    default=None,
    help="read (possibly additional) inputs from file",
    )
parser.add_argument( 
    "-g", "--origin",
    default=None,
    help="what to call the master header (row1, col1)",
    )
parser.add_argument(
    "-m", "--mode",
    choices=["piped", "piped_humann"],
    help="special sorting options",
    )
args = parser.parse_args()

# ---------------------------------------------------------------
# load all data
# ---------------------------------------------------------------

dictTableData = {}
# modified for faster looking up 4/2/2015
dictFeatureIndex = {}

say( "Will load:", len( args.inputs ), "gathered from command line" )

if args.file is not None:
    before = len( args.inputs )
    with open( args.file ) as fh:
        for line in fh:
            args.inputs.append( line.strip() )
    after = len( args.inputs )
    say( "Will load:", after - before, "additional files gathered from:", args.file )

for iDex, strPath in enumerate( args.inputs ):
    say( sys.stderr, "Loading", iDex+1, "of", len( args.inputs ), ":", strPath )
    aastrData = []
    strColhead = path2name( strPath )
    with open( strPath ) as fh:
        for astrItems in reader( fh ):
            aastrData.append( [astrItems[args.key_col], astrItems[args.val_col]] ),
    if args.strip_comments:
        aastrData = [ astrRow for astrRow in aastrData if astrRow[0][0] != "#" ]
    if args.use_headers:
        strColhead = aastrData[0][1]
    if args.strip_headers:
        aastrData = aastrData[1:]
    if args.key_pattern:
        aastrData = [ astrRow for astrRow in aastrData if re.search( args.key_pattern, astrRow[0] ) ]
    for strFeature, strValue in aastrData:
        if strFeature not in dictFeatureIndex:
            dictFeatureIndex[strFeature] = len( dictFeatureIndex ) + 1
    dictTableData[strColhead] = {strKey:strValue for [strKey, strValue] in aastrData}

# ---------------------------------------------------------------
# coerce to table
# ---------------------------------------------------------------

# not ideal
kwargs={"empty":args.fill_empty} if args.fill_empty is not None else { }

# feature ordering (implemented 4/2015 for unknown reason; modified as non-default 1/2016)
if args.mode is None:
    astrFeatures = sorted( dictFeatureIndex.keys() )
elif args.mode == "piped":
    astrFeatures = sorted( dictFeatureIndex.keys( ), key=lambda x: x.split( "|" ) )
elif args.mode == "piped_humann":
    special = {
        "UNMAPPED":0, 
        "UNGROUPED":1, 
        "UNINTEGRATED":2, 
        "UniRef90_unknown":3, 
        "UniRef50_unknown":4, 
        }
    default = 1 + max( special.values( ) )
    astrFeatures = sorted( dictFeatureIndex.keys( ), key=lambda x: x.split( "|" ) )
    astrFeatures = sorted( astrFeatures, key=lambda x: special.get( x.split( "|" )[0], default ) )

# convert to table ***note: sample is first key == rowhead (until transpose) ***
tableData = nesteddict2table( dictTableData, aColheads=astrFeatures, **kwargs )
tableData.rowsort( )
tableData.transpose()

# replace origin?
if args.origin is not None:
    tableData.data[0][0] = args.origin

# not ideal
if args.output is not None:
    tableData.dump( args.output )
else:
    tableData.dump()
