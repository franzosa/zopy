#! /usr/bin/env python

"""
Plots zero-inflated log-log data
"""
    
"""
assume we're getting input like...
X  Y  color s zorder ...
1  2  red   3 1
2  3  blue  3 2
9  0  red   2 1

X and Y become the axis labels. All other columns are optional,
but will be converted to scatter kwargs if given. Default is to leave
them as strings unless header is in the floatable fields list.
"""

import os, sys, re, glob, argparse
import matplotlib as mpl
mpl.use( "Agg" )
import matplotlib.pyplot as plt
from zopy.zillplot import zillplot
from zopy.utils import reader

aFloatableFields = ["s", "alpha", "zorder"]
# argument parsing ( python argparse )
parser = argparse.ArgumentParser()
parser.add_argument( '-i', '--input', help='' )
parser.add_argument( '-o', '--output', help='' )
parser.add_argument( '-n', '--logmin', type=float, help='' )
parser.add_argument( '-x', '--logmax', type=float, help='' )
args = parser.parse_args()

# parse the input file for x,y values and kwargs    
aX, aY = [], []
kwargs = {}
with open( args.input ) as fh:
    aHeaders = fh.readline().strip().split( "\t" )
    for aItems in reader( fh ):
        aX.append( float( aItems[0] ) )
        aY.append( float( aItems[1] ) )
        if len( aItems ) > 2:
            for i, value in enumerate( aItems[2:] ):
                header = aHeaders[i+2]
                value = float( value ) if header in aFloatableFields else value
                kwargs.setdefault( header, [] ).append( value )

# execute plot
fig = plt.figure()
fig.set_size_inches( 5, 5 )
ax = plt.subplot( 111 )

# note: if args.logmin/max not specified, they will pass None ( which ZillPlot expects )
zillplot( ax, aX, aY, logmin=args.logmin, logmax=args.logmax, **kwargs )
ax.set_xlabel( aHeaders[0] )
ax.set_ylabel( aHeaders[1] )
plt.tight_layout()
plt.savefig( args.output, format=args.output.split( "." )[-1] )
