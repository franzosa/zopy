#!/usr/bin/env python

"""
Mosaic Plot: A heatmap alternative
===============================================
Author: Eric Franzosa (eric.franzosa@gmail.com)
"""

import os
import sys
import re
import csv
import math
import argparse
import matplotlib
matplotlib.use( "Agg" )
import matplotlib.pyplot as plt
import matplotlib.patches as patches

from zopy.table2 import table
import zopy.mplutils as mu
import zopy.dictation as dd

# ---------------------------------------------------------------
# Constants
# ---------------------------------------------------------------

c_fadeout = 0.2
c_colw = 1.0
c_rowh = 0.25
c_rowlabw = 4.0
c_collabh = 1.0

# ---------------------------------------------------------------
# cli
# ---------------------------------------------------------------

def get_args( ):
    parser = argparse.ArgumentParser()
    parser.add_argument( "table",
                         help="input table; heatmap style",
    )
    parser.add_argument( "-c", "--colormap",
                         default="jet",
                         help="colormap for columns",
    )
    parser.add_argument( "-e", "--emphasis",
                         choices=["fade", "dot", "none"],
                         default="none",
                         help="fade out non-max entries in each row",
    )
    parser.add_argument( "-s", "--scale",
                         type=int,
                         default=2,
                         help="scale data as x^(1/s), (default s=2; assumes area scaling)",
    )
    parser.add_argument( "-m", "--mode",
                         choices=["area", "width", "height"],
                         default="area",
                         help="scale box area or only width (default=area)",
    )
    parser.add_argument( "-g", "--grid",
                         choices=["box", "cross"],
                         default="box",
                         help="style of grid",
    )
    parser.add_argument( "-o", "--outfile",
                         default="figure.pdf",
    )
    args = parser.parse_args()
    return args
                    
# ---------------------------------------------------------------
# utils
# ---------------------------------------------------------------

def argmax( d ):
    mk, mv = None, None
    for k, v in d.items():
        if mv is None or v > mv:
            mk, mv = k, v
    return mk

def nearest_power( n, p ):
    return math.floor( math.log( n ) / math.log( p ) )

# ---------------------------------------------------------------
# main
# ---------------------------------------------------------------

def main( ):
    args = get_args( )
    t = table( args.table )
    t.float()
    # apply scaling
    gmax = max( [max( row ) for header, row in t.iter_rows()] )
    t.apply_entries( lambda x: (x / gmax)**(1/float( args.scale )) )
    # format labels
    xlab = sorted( t.colheads )
    ylab = sorted( t.rowheads, key=lambda x: argmax( t.rowdict( x ) ), reverse=True )
    # make plot
    colors = mu.ncolors( len( xlab ), args.colormap )
    fig = plt.figure()
    axes = mu.funcPlotMatrix( [1], [len( t.rowheads ), 2] )
    ax = axes[0][0]
    legend = axes[1][0]
    ax.xaxis.tick_top()
    ax.yaxis.tick_right()
    ax.set_xticks( range( len( xlab ) ) )
    ax.set_yticks( range( len( ylab ) ) )
    ax.set_xticklabels( xlab, rotation=45, rotation_mode="anchor", ha="left" )
    ax.set_yticklabels( ylab )
    ax.set_xlim( -0.5, len( xlab ) - 0.5 ) 
    ax.set_ylim( -0.5, len( ylab ) - 0.5 ) 
    # add tiles
    for i, x in enumerate( xlab ):
        for j, y in enumerate( ylab ):
            value = t.entry( y, x )
            if value == 0:
                continue           
            tileh = 1.0 if args.mode == "width" else value
            tilew = 1.0 if args.mode == "height" else value
            alpha = 1.0
            if args.emphasis=="fade" and argmax( t.rowdict( y ) ) != x:
                alpha = c_fadeout
            ax.add_patch(
                patches.Rectangle(
                    (i-tilew/2.0, j-tileh/2.0),
                    tilew,
                    tileh,
                    edgecolor="white",
                    facecolor=colors[i],
                    alpha=alpha,
                )
            )
            if args.emphasis=="dot" and argmax( t.rowdict( y ) ) == x:
                ax.scatter( [i], [j], s=10, color="white", edgecolor="none", zorder=2 )
    # add grid
    if args.grid == "box":
        mu.funcGrid2(
            ax,
            h=[k-0.5 for k in range( 1, len( ylab ) )],
            v=[k-0.5 for k in range( 1, len( xlab ) )],        
            color="0.9",
            zorder=2,
            border=True,
        )
    elif args.grid == "cross":
        mu.funcGrid2(
            ax,
            h=[k for k in range( len( ylab ) )],
            v=[k for k in range( len( xlab ) )],
            color="0.9",
            zorder=0,
            border=True,
        )
        mu.funcHideBorder( ax )
    # cleanup
    mu.funcHideTicks( ax )
    # draw the legend
    mu.funcSetTickParams( legend )
    #mu.funcHideBorder( legend )
    legend.yaxis.tick_right( )
    legend.set_yticks( [0] )
    legend.set_yticklabels( ["Scale"] )
    legend.set_xlim( -0.5, len( xlab ) - 0.5 ) 
    legend.set_xticks( range( len( xlab ) ) )
    legend.set_ylim( -0.5, 0.5 )
    start = nearest_power( gmax, 10 )
    values = [(10**start) * 0.1**i for i in range( len( xlab ) )]
    values = [(gmax) * 0.1**i for i in range( len( xlab ) )]
    values.reverse( )
    legend.set_xticklabels( ["%.2g" % k for k in values] )
    j = 0
    for i, value in enumerate( values ):
        value = (value / gmax)**(1/float( args.scale ))
        tileh = 1.0 if args.mode == "width" else value
        tilew = 1.0 if args.mode == "height" else value
        legend.add_patch(
            patches.Rectangle(
                (i-tilew/2.0, j-tileh/2.0),
                tilew,
                tileh,
                edgecolor="none",
                facecolor="0.5",
            )
        )
    # finalize
    fig.set_size_inches(
        c_colw * len( xlab ) + c_rowlabw,
        c_rowh * ( 1 + len( ylab ) ) + c_collabh,
    )
    plt.tight_layout()
    plt.savefig( args.outfile )

if __name__ == "__main__":
    main( )    
