#! /usr/bin/env python

"""
Module for making "ZILL" ( Zero-Inflated Log-log ) plots
---------------------------------------
Eric Franzosa ( eric.franzosa@gmail.com )
"""

import os
import sys
import re
import glob
import argparse
from math import log10

import numpy as np
import matplotlib as mpl
mpl.use( "Agg" )
import matplotlib.pyplot as plt

import zopy.mplutils2 as mu
from zopy.utils import reader, say

# ---------------------------------------------------------------
# constants
# ---------------------------------------------------------------

c_dash_size = 75
c_margin = 0.05

# ---------------------------------------------------------------
# set up the plotting area
# ---------------------------------------------------------------

def zillplot_area( ax, xx, yy, xlims=None, ylims=None ):
    """ set up the plotting area """
    # decide how to scale axes
    xlims = xlims if xlims is not None else mu.logminmax( xx )
    ylims = ylims if ylims is not None else mu.logminmax( yy )
    xlims = list( xlims )
    ylims = list( ylims )
    # set up x system
    xmin, xmax = [np.log10( k ) for k in xlims]
    xdiff = xmax - xmin
    expander = 2 if min( xx ) == 0 else 1
    xzero    = 10**( xmin - c_margin * xdiff )
    xlims[0] = 10**( xmin - c_margin * xdiff * expander )
    xlims[1] = 10**( xmax + c_margin * xdiff )
    # set up y system
    ymin, ymax = [np.log10( k ) for k in ylims]
    ydiff = ymax - ymin
    expander = 2 if min( yy ) == 0 else 1
    yzero    = 10**( ymin - c_margin * ydiff )
    ylims[0] = 10**( ymin - c_margin * ydiff * expander )
    ylims[1] = 10**( ymax + c_margin * ydiff )
    # configure axes
    mu.tick_params( ax )
    ax.set_xscale( "log" )
    ax.set_yscale( "log" )
    ax.set_xlim( xlims[0], xlims[1] )
    ax.set_ylim( ylims[0], ylims[1] )
    mu.trim_minor_ticks( ax )
    # add a default grid
    ax.set_axisbelow( True )
    ax.grid( which="major", axis="both", color="0.95", linestyle="-", linewidth=1.0, zorder=-1 )
    # the point plotter needs to know this
    return xzero, yzero

# ---------------------------------------------------------------
# plot the points
# ---------------------------------------------------------------

def index( xx, yy ):
    """ provides the index positions of ( 0,y ) ( x,0 ) and ( 0,0 ) points """
    xzeroes = []
    yzeroes = []
    nonzero = []
    discard = 0
    for i, (x, y) in enumerate( zip( xx, yy ) ):
        if x > 0 and y > 0:
            nonzero.append( i )
        elif x > 0 and y == 0:
            yzeroes.append( i )
        elif y > 0 and x == 0:
            xzeroes.append( i )
        else:
            discard += 1
    if discard > 0:
        say( "zillplot ignoring", discard, "( 0,0 ) points" )
    return xzeroes, yzeroes, nonzero

def subvector( xx, index ):
    """ perform a slice of a vector based on index positions """
    return [xx[i] for i in index]

def scatter( ax, xx, yy, xzero=None, yzero=None, **kwargs ):
    """ add the point; needs to inherit zero location from Area function """
    xzeroes, yzeroes, nonzero = index( xx, yy )
    # plot the nonzero points
    xx2 = subvector( xx, nonzero )
    yy2 = subvector( yy, nonzero )
    ax.scatter( xx2, yy2, **kwargs )
    # plot the zero-x points ( note kwarg overrides )
    kwargs["marker"] = "_"
    kwargs["edgecolor"] = kwargs["color"]
    kwargs["s"] = c_dash_size if "s" not in kwargs else kwargs["s"]
    xx2 = [xzero for k in xzeroes]
    yy2 = subvector( yy, xzeroes )
    ax.scatter( xx2, yy2, **kwargs )
    # plot the zero-y points ( note kwarg overrides )
    kwargs["marker"] = "|"
    xx2 = subvector( xx, yzeroes )
    yy2 = [yzero for k in yzeroes]
    ax.scatter( xx2, yy2, **kwargs )

# ---------------------------------------------------------------
# main function
# ---------------------------------------------------------------

def zillplot( ax, xx, yy, xlims=None, ylims=None, color="cornflowerblue", edgecolor="none", alpha=0.5, **kwargs ):
    """ the main function; call this if importing into other scripts """
    # set up plot area and retrieve zero position
    xzero, yzero = zillplot_area( ax, xx, yy, xlims=xlims, ylims=ylims )
    # plot points
    scatter( ax, xx, yy, xzero=xzero, yzero=yzero, color=color, edgecolor=edgecolor, alpha=alpha, **kwargs )
