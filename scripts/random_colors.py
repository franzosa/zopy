#!/usr/bin/env python

import sys
import random
import argparse

import matplotlib
matplotlib.use( "Agg" )
import matplotlib.pyplot as plt

from zopy.utils import iter_rows, warn

# argument parsing (python argparse)
parser = argparse.ArgumentParser( )
parser.add_argument( "mapping", help="" )
parser.add_argument( "--cmap", default="Paired", help="" )
parser.add_argument( "--prioritize", default=15, type=int, help="" )
parser.add_argument( "--max-colors", default=None, type=int, help="" )
parser.add_argument( "--seed", default=1701, type=int, help="" )
args = parser.parse_args( )

random.seed( args.seed )

c_cmap = args.cmap
c_ntop = args.prioritize
c_nmax = args.max_colors

pairs = []
for row in iter_rows( args.mapping ):
    if len( row ) == 1:
        pairs.append( [0, row[0]] )
    else:
        pairs.append( [-float( row[1] ), row[0]] )
pairs.sort( )

cmap = plt.get_cmap( c_cmap )
cmap_max = cmap.N

# get evenly spaced colors for the top n features
even = [cmap( int( k * cmap_max / (c_ntop - 1) ) ) for k in range( c_ntop )]
random.shuffle( even )

colors = {}
for i, pair in enumerate( pairs ):
    feature = pair[1]
    if i < c_ntop:
        colors[feature] = even[i]
    # note: you can't go higher than the number of discrete colors in the colormap
    elif (c_nmax is None or i < c_nmax) and (i < cmap_max):
        color = None
        while color is None or color in colors.values( ):
            color = cmap( int( random.random( ) * cmap_max ) )
        colors[feature] = color

r = lambda x: int( x * 255 )
for feature, color in colors.items( ):
    print "%s\t#%02X%02X%02X" % ( feature, r( color[0] ), r( color[1] ), r( color[2] ) )
