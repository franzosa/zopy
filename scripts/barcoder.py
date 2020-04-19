#! /usr/bin/env python

"""
Makes MetaPhlAn Marker Barcodes
Eric Franzosa (eric.franzosa@gmail.com)
"""
    
"""
Requires an input PCL file from scriptConvertCladeProfiles.py
Should look like:

headers        sample1 sample2 sample3 ...
clade1|marker1     0.3     0.5     0.2
clade1|marker2     0.3     0.5     0.2
clade2|marker1     0.3     0.5     0.2
clade2|marker2     0.3     0.5     0.2
"""

import os, sys, re, glob, argparse
import matplotlib.pyplot as plt
from zopy.barcoder import barcoder
import zopy.mplutils as mu
from zopy.table2 import table

# argument parsing ( python argparse )
parser = argparse.ArgumentParser()
parser.add_argument( '-i', '--input',     default=None,                      help='Marker PCL file (like output of scriptConvertCladeProfiles.py)' )
parser.add_argument( '-c', '--clades',    default=None,           nargs="+", help='List or file of clades to barcode (default <all>)' )
parser.add_argument( '-s', '--samples',   default=None,           nargs="+", help='List or file of samples to include (default <all>)' )
parser.add_argument( '-k', '--scaling',   default="binary",                  help='Scaling method (<binary>, bins, norm, rownorm, lognorm, rowlognorm)' )
parser.add_argument( '-b', '--bins',      default=None,           nargs="+", help='List or file of bins for binning (if scaling=bins)' )
parser.add_argument( '-y', '--highlight', default=None,           nargs="+", help='List or file of markers to highlight (default <none>)' )
parser.add_argument( '-o', '--output',    default="barcodes.pdf",            help='Name for the figure' )
args = parser.parse_args() 

# utility
def funcArgPathCheck ( astrPolyArgument ):
    if astrPolyArgument is None:
        return None
    elif os.path.exists( astrPolyArgument[0] ):
        with open( astrPolyArgument[0] ) as fh:
            return [strLine.strip() for strLine in fh]
    else:
        return astrPolyArgument

# fixed constants
c_fWidth = 6.0
c_fMinorHeight = 0.4
c_strColor1 = "0.40"
c_strColor2 = "0.60"
c_strBackgroundColor = "0.95"

# constants from args
c_pathPCL = args.input
c_astrSamples = funcArgPathCheck( args.samples )
c_astrClades = funcArgPathCheck( args.clades )
c_strScaling = args.scaling
c_afBins = funcArgPathCheck( args.bins )
if c_afBins is not None:
    c_afBins = [float( k ) for k in c_afBins]
    c_afBins.sort()
c_astrHighlight = funcArgPathCheck( args.highlight )

# load and manipulate table
tableData = table( c_pathPCL )
tableData.float()
if c_astrClades is not None:
    tableData.grep( "headers", c_astrClades )
if c_astrSamples is not None:
    tableData.select( "headers", c_astrSamples, transposed=True )
dictCladeTables = tableData.groupify( lambda strRowhead: strRowhead.split( "|" )[0] )

# override these lists based on what was in the table
c_astrClades = dictCladeTables.keys()
c_astrSamples = tableData.colheads[:]

# derived constants
c_iClades = len( c_astrClades )
c_iSamples = len( c_astrSamples )
c_fHeight = c_fMinorHeight * c_iClades * c_iSamples

# execute plot
fig = plt.figure()
fig.set_size_inches( c_fWidth, c_fHeight )
aaAxes = mu.funcPlotMatrix( [1], [1 for k in range( c_iClades )] )

# plotting
for iDex, strClade in enumerate( c_astrClades ):
    Axes = aaAxes[iDex][0]
    # build the matrix
    aafData = []
    aabHighlight = []
    astrLabels = []
    astrColors = []
    for strSample in c_astrSamples:
        astrLabels.append( strSample )
        aafData.append( dictCladeTables[strClade].col( strSample ) )
        aabHighlight.append( [True if ( c_astrHighlight is not None and k in c_astrHighlight ) else False for k in dictCladeTables[strClade].rowheads] )
        astrColors.append( c_strColor1 if len( astrColors ) == 0 or astrColors[-1] == c_strColor2 else c_strColor2 )
    # make a barcode
    barcoder( Axes, 
              aafData, 
              aaHighlight=aabHighlight, 
              aLabels=astrLabels, 
              scaling=c_strScaling, 
              bins=c_afBins,
              color=astrColors, 
              background=c_strBackgroundColor,
              show_xticks=False,
              )
    Axes.set_title( strClade.replace( "s__", "" ).replace( "_", " " ), size=9, style="italic" )
    Axes.set_ylabel( "Samples", size=9 )

# cleanup
plt.tight_layout()
plt.savefig( args.output, format=args.output.split( "." )[-1] )
