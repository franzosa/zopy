#! /usr/bin/env python

import os, sys, re, glob, argparse
import matplotlib.pyplot as plt
from zopy.table2 import table
import zopy.mplutils as mu
import zopy.utils as utils
from zopy.stepplot import stepplot

# ---------------------------------------------------------------
# argparse
# ---------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument( '--input', help='' )
parser.add_argument( '--output', help='' )
parser.add_argument( '--logmin', type=float, help='' )
parser.add_argument( '--logmax', type=float, help='' )
args = parser.parse_args()

# ---------------------------------------------------------------
# main
# ---------------------------------------------------------------

# get and manipulate data
t = table( args.input )
t.apply_entries( lambda x: None if x == "" else x )
t.apply_entries( lambda x: float( x ) if x is not None else None )

# derived features
aColors = [plt.cm.Dark2( i / float( len( t.colheads ) ) ) for i, colhead in enumerate( t.colheads )]
aaData = [row for rowhead, row in t.iter_rows()]
logmin, logmax = args.logmin, args.logmax

# make plot
fig = plt.figure()
axes = plt.subplot( 111 )
stepplot( axes, aaData, colors=aColors )

# configure
axes.set_yscale( "log" )
axes.set_ylim( logmin, logmax )
axes.xaxis.set_ticklabels( t.colheads, rotation=35, rotation_mode="anchor", ha="right" )
axes.set_title( utils.path2name( args.input ) )
axes.set_ylabel( "Relative abundance" )
mu.funcGrid( axes, xaxis=False, color="gray", linestyle=":" )
mu.funcSetTickParams( axes )

# done
plt.tight_layout()
plt.savefig( args.output )
