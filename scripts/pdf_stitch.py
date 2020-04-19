#! /usr/bin/env python

"""
Combine multiple PDF panels of the same size as one figure
Uses linux tools pdfnup (from pdfjam) and pdfinfo
"""

import os, sys, re, glob, argparse
import subprocess

# argument parsing (python argparse)
parser = argparse.ArgumentParser()
parser.add_argument( '-i', '--input',  nargs="+", help='' )
parser.add_argument( '-o', '--output', default="stitched.pdf", help='' )
parser.add_argument( '-r', '--rows',   default=None, help='' )
parser.add_argument( '-c', '--cols',   default=None, help='' )
args = parser.parse_args()

# deal with args
astrPaths = args.input
strOutfile = args.output
iRows = int( args.rows ) if args.rows is not None else len( astrPaths )
iCols = int( args.cols ) if args.rows is not None else 1
if iRows * iCols != len( astrPaths ):
    sys.exit( "dimension mismatch" )

# get the size of the pdfs
aafSizes = []
for strPath in astrPaths:
    cmd = subprocess.Popen( 'pdfinfo %s' % ( strPath ), shell=True, stdout=subprocess.PIPE)
    for line in cmd.stdout:
        Match = re.search( "Page size:      (.*) x (.*) pts", line ) 
        if Match:
            fW = float( Match.group( 1 ) ) / 72.0 # dots per inch
            fH = float( Match.group( 2 ) ) / 72.0 
            aafSizes.append( (fW, fH) )
            print strPath, aafSizes[-1]
if len( set( aafSizes ) ) != 1:
    sys.exit( "not all panels are the same size" )

# merge command and run
astrCommand = [
    "pdfjam",
    "--no-landscape",
    "--nup", "%dx%d" % ( iCols, iRows ),
    "--papersize", "'{%din,%din}'" % ( fW * iCols, fH * iRows ),
    "--outfile", strOutfile,
    " ".join( astrPaths ),
]
os.system( " ".join( astrCommand ) )
