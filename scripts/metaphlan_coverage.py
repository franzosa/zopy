#! /usr/bin/env python

"""
Use MetaPhlAn clade profiles output to estimate bug coverage, rpk, and rpkm
Requires a clade profiles PCL from zopy/scripts/scriptConvertCladeProfiles.py
=====
Author: Eric Franzosa (eric.franzosa@gmail.com)
"""

import os, sys, re, glob, argparse
from numpy import median
from zopy.table2 import table
from zopy.dictation import col2dict

# ---------------------------------------------------------------
# argument parsing
# ---------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument( 
    "-i", "--input", 
    help="clade profiles PCL",
)
parser.add_argument( 
    "-m", "--mode",
    default="rpk",
    choices=["rpk", "coverage", "rpkm"],
    help="rpk, coverage, or rpkm (requires additional file)",
)
parser.add_argument( 
    "-r", "--sample_reads",
    default=None,
    help="file mapping sample IDs to read counts",
)
parser.add_argument( 
    "-l", "--read_length",
    type=float,
    default=100.0,
    help="read length for coverage estimation",
)
parser.add_argument( 
    "-o", "--output",
    default=None,
    help="output file name",
)
args = parser.parse_args()

# ---------------------------------------------------------------
# handle arguments
# ---------------------------------------------------------------

strInputPath = args.input
strMode = args.mode
strOutputPath = args.output if args.output is not None else ".".join( strInputPath, strMode )
fReadLength = args.read_length
strSampleReadsPath = args.sample_reads

# ---------------------------------------------------------------
# manipulate data
# ---------------------------------------------------------------

if strMode == "rpkm":
    if strSampleReadsPath is None:
        sys.exit( "to compute rpkm you must include a file mapping sample IDs to #s of reads" )
    dictMillions = col2dict( strSampleReadsPath, key=0, value=1, func=lambda x: float( x ) / 1e6 )

tableCladeRPK = table( strInputPath )
tableCladeRPK.grep( "headers", "s__" )
tableCladeRPK.float()
tableCladeRPK.groupby( lambda x: x.split( "|" )[0], median )

if strMode != "rpk":
    for bug, sample, value in tableCladeRPK.iter_entries():
        if strMode == "coverage":
            tableCladeRPK.set( bug, sample, value * fReadLength / 1e3 )
        elif strMode == "rpkm":
            tableCladeRPK.set( bug, sample, value / dictMillions[sample] if dictMillions[sample] > 0 else 0 )

tableCladeRPK.unfloat()
tableCladeRPK.colsort()
tableCladeRPK.rowsort()
tableCladeRPK.dump( strOutputPath )
