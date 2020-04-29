#! /usr/bin/env python

import os
import sys
from collections import Counter
from random import random
from math import floor, ceil, log

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

#-------------------------------------------------------------------------------
# constants
#-------------------------------------------------------------------------------

c_dcolor = "cornflowerblue"

#-------------------------------------------------------------------------------
# utilities
#-------------------------------------------------------------------------------

def shatter( labels, values ):
    data = {}
    for l, v in zip( labels, values ):
        data.setdefault( l, [] ).append( v )
    return data

def ncolors( n, colormap="jet" ):
    """utility for defining N evenly spaced colors across a color map"""
    cmap = plt.get_cmap( colormap )
    cmap_max = cmap.N
    if n > 1:
        return [cmap( int( k * cmap_max / (n - 1) ) ) for k in range( n )]
    else:
        return [cmap( 0.5 )]  

def ncolormap( mapping, n=7, colormap="jet", 
               other_label="Other", other_color="0.5" ):
    ncolormap = {other_label:other_color}
    counts = Counter( mapping.values( ) )
    colors = ncolors( n, colormap=colormap )
    i = 0
    for v in sorted( counts, key=lambda x: -counts[x] ):
        if i < n:
            ncolormap[v] = colors[i]
        i += 1
    for k, v in mapping.items( ):
        if v not in ncolormap:
            mapping[k] = other_label
    return mapping, ncolormap

#-------------------------------------------------------------------------------
# new approach 
#-------------------------------------------------------------------------------

class Plotrix:

    def __init__( self, widths=None, heights=None, lwidth=1 ):

        self.axes = []
        self.axmap = {}
        self.legend = None
        self.r = len( heights )
        self.c = len( widths )
        
        cmax = sum( widths ) + lwidth
        rmax = sum( heights )
        rdex = 0

        # define plots
        for r, height in enumerate( heights ):
            axrow = []
            cdex = 0
            for c, width in enumerate( widths ):
                axrow.append(
                    plt.subplot2grid(
                        ( rmax, cmax ),
                        ( rdex, cdex ),
                        rowspan=heights[r],
                        colspan=widths[c],
                        )
                    )
                cdex += widths[c]
            self.axes.append( axrow )
            rdex += heights[r]
            
        # define legend
        if lwidth > 0:
            self.legend = plt.subplot2grid(
                ( rmax, cmax ),
                ( 0   , cdex ),
                rowspan=sum( heights ),
                colspan=lwidth,
            )
            
    def name( self, r, c, name ):
        self.axmap[name] = (r, c)

    def index( self, r, c ):
        return self.axes[r][c]
        
    def lookup( self, name ):
        return self.axmap[name]

    def iter_axes( self ):
        for r in range( self.r ):
            for c in range( self.c ):
                yield r, c, self.axes[r][c]

    def apply_axes( self, function, rows=None, cols=None, *args, **kwargs ):
        for r, c, ax in self.iter_axes( ):
            if rows is None or r in rows:
                if cols is None or c in cols:
                    function( ax, *args, **kwargs )
                
#-------------------------------------------------------------------------------
# axis systems and operations
#-------------------------------------------------------------------------------
    
def plotrix( widths, heights ):
    axes = []
    cmax = sum( widths )
    rmax = sum( heights )
    rdex = 0
    for i, height in enumerate( heights ):
        row = []
        cdex = 0
        for j, width in enumerate( widths ):
            row.append( 
                plt.subplot2grid( 
                    ( rmax, cmax ), 
                    ( rdex, cdex ), 
                    rowspan=heights[i], 
                    colspan=widths[j], 
                ) 
            )
            cdex += widths[j]
        axes.append( row )
        rdex += heights[i]
    return axes

def iter_axes( axes ):
    """ generator """
    for axrow in axes:
        for ax in axrow:
            yield ax

def apply_axes( axes, func, **kwargs ):
    for ax in iter_axes( axes ):
        func( ax, **kwargs )

#-------------------------------------------------------------------------------
# ax style
#-------------------------------------------------------------------------------

def tick_params( ax, **kwargs ):
    """ Converts ticks from default matplotlib to default eric style """
    # major minor x
    ax.tick_params( axis="x", which="major",
                    direction="out", bottom="on", top="off", width=1.0,
                    **kwargs )
    ax.tick_params( axis="x", which="minor",
                    direction="out", bottom="on", top="off", width=1.0,
                    **kwargs )
    # major minor y
    ax.tick_params( axis="y", which="major", direction="out",
                    left="on", right="off", width=1.0, **kwargs )
    ax.tick_params( axis="y", which="minor", direction="out",
                    left="on", right="off", width=1.0, **kwargs )

def hide_xticks( ax ):
    for t in ax.xaxis.get_major_ticks( ): 
        t.tick1On = False 
        t.tick2On = False

def hide_yticks( ax ):
    for t in ax.yaxis.get_major_ticks( ): 
        t.tick1On = False
        t.tick2On = False

def resize_xticklabels( ax, size ):
    for t in ax.xaxis.get_major_ticks( ):
        t.label.set_fontsize( size )
        
def resize_yticklabels( ax, size ):
    for t in ax.yaxis.get_major_ticks( ):
        t.label.set_fontsize( size )

def hide_xaxis( ax, major=True, minor=True ):
    """ Hides all x axis elements """
    if major:
        [ label.set_visible( False ) for label in ax.get_xticklabels() ]
        [ tick.set_visible( False )  for tick  in ax.xaxis.get_major_ticks() ]
    if minor:
        [ tick.set_visible( False )  for tick  in ax.xaxis.get_minor_ticks() ]

def hide_yaxis( ax, major=True, minor=True ):
    """ Hides all y axis elements """
    if major:
        [ label.set_visible( False ) for label in ax.get_yticklabels() ]
        [ tick.set_visible( False )  for tick  in ax.yaxis.get_major_ticks() ]
    if minor:
        [ tick.set_visible( False )  for tick  in ax.yaxis.get_minor_ticks() ]

def trim_minor_ticks( ax ):
    """ removes minor ticks outside of first, last major tick """
    # xaxis
    MM = ax.xaxis.get_majorticklocs( )
    mm = ax.xaxis.get_minorticklocs( )
    bb = ax.get_xlim( )
    MM = [M for M in MM if bb[0] <= M <= bb[1]]    
    for t, m in zip( ax.xaxis.get_minor_ticks( ), mm ):
        if not (MM[0] < m < MM[-1]):
            t.set_visible( False )
    # yaxis        
    MM = ax.yaxis.get_majorticklocs( )
    mm = ax.yaxis.get_minorticklocs( )
    bb = ax.get_ylim( )
    MM = [M for M in MM if bb[0] <= M <= bb[1]]    
    for t, m in zip( ax.yaxis.get_minor_ticks( ), mm ):
        if not (MM[0] < m < MM[-1]):
            t.set_visible( False )
        
def border( ax, **kwargs ):
    """ apply general properties to the border """
    plt.setp( [child for child in ax.get_children() \
               if isinstance( child, mpl.spines.Spine )], **kwargs )

def hide_border( ax, half=False ):
    """ hides the border of a plot; surprisingly tricky """
    c = 0
    for child in ax.get_children( ):
        if isinstance( child, mpl.spines.Spine ):
            c += 1
            if not half or c not in [3, 4]:
                plt.setp( child, visible=False )
    
def dummy( ax ):
    """ leaves an empty plot in a grid """
    ax.patch.set_facecolor( "none" )
    hide_xaxis( ax )
    hide_yaxis( ax )
    hide_border( ax )
    
def xbounded( ax, k ):
    l1, l2 = ax.get_xlim( )
    return l1 < k < l2

def ybounded( ax, k ):
    l1, l2 = ax.get_ylim( )
    return l1 < k < l2
    
def tick_grid( ax, xaxis=True, yaxis=True, xy=False, minor=False, \
               color="0.95", linestyle="-", zorder=0, **kwargs ):
    """ Makes a grid that doesn't depend on x,y visibility """
    # embed extra options in kwargs
    kwargs["color"] = color
    kwargs["linestyle"] = linestyle
    kwargs["zorder"] = zorder
    xlocs = ax.xaxis.get_majorticklocs() if not minor else ax.xaxis.get_minorticklocs()
    ylocs = ax.yaxis.get_majorticklocs() if not minor else ax.yaxis.get_minorticklocs()
    xmin, xmax = ax.get_xlim( )
    ymin, ymax = ax.get_ylim( )
    if xaxis:
        for x in xlocs:
            ax.add_line( plt.Line2D( [x, x], [ymin, ymax], **kwargs ) )
    if yaxis:
        for y in ylocs:
            ax.add_line( plt.Line2D( [xmin, xmax], [y, y], **kwargs ) )
    if xy:
        minmin = min( xmin, ymin )
        minmax = min( xmax, ymax )
        ax.add_line( plt.Line2D( [minmin, minmax], [minmin, minmax], **kwargs ) )
       
def user_grid( ax, h=None, v=None, color="0.95", zorder=0, **kwargs ):
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    # embed extra options in kwargs
    kwargs["color"] = color
    kwargs["zorder"] = zorder
    if h is not None:
        for y in h:
            if ybounded( ax, y ):
                ax.add_line( plt.Line2D( [xmin, xmax], [y, y], **kwargs ) )
    if v is not None:
        for x in v:
            if xbounded( ax, x ):
                ax.add_line( plt.Line2D( [x, x], [ymin, ymax], **kwargs ) )

def hide_inner_axes( axes, simplify=False ):
    """ only show the outer grid axes """
    for i, axrow in enumerate( axes ):
        for j, ax in enumerate( axrow ):
            if i+1 < len( axes ):
                hide_xaxis( ax )
                ax.set_xlabel( "" )
            if j > 0:
                hide_yaxis( ax )
                ax.set_ylabel( "" )
            if simplify and ( i+1 < len( axes ) or j != 0 ):
                # only label axes at the bottom left corner
                ax.set_xlabel( "" )
                ax.set_ylabel( "" )

def row_lims( axes ):
    for row in axes:
        gmin, gmax = row[0].get_ylim( )
        for ax in row:
            lmin, lmax = ax.get_ylim( )
            gmin = min( gmin, lmin )
            gmax = max( gmax, lmax )
        for ax in row:
            ax.set_ylim( gmin, gmax )

def col_lims( axes ):
    for i in range( len( axes[0] ) ):
        col = [row[i] for row in axes]
        gmin, gmax = row[0].get_ylim( )
        for ax in col:
            lmin, lmax = ax.get_xlim( )
            gmin = min( gmin, lmin )
            gmax = max( gmax, lmax )
        for ax in col:
            ax.set_xlim( gmin, gmax )
                
def common_limits( axes, forcex=True, forcey=True, symx=False, symy=False ):
    """ enforce common mins and maxes """
    # get
    gxmin, gxmax, gymin, gymax = None, None, None, None
    for ax in iter_axes( axes ):
        xmin, xmax = ax.get_xlim()
        gxmin = xmin if gxmin is None or xmin < gxmin else gxmin
        gxmax = xmax if gxmax is None or xmax > gxmax else gxmax
        ymin, ymax = ax.get_ylim()
        gymin = ymin if gymin is None or ymin < gymin else gymin
        gymax = ymax if gymax is None or ymax > gymax else gymax
    # symmetry
    if gxmin < 0 < gxmax and symx:
        v = max( abs( gxmin ), gxmax )
        gxmin, gxmax = -v, v
    if gymin < 0 < gymax and symy:
        v = max( abs( gymin ), gymax )
        gymin, gymax = -v, v
    # set
    for ax in iter_axes( axes ):
        if forcex:
            ax.set_xlim( gxmin, gxmax )
        if forcey:
            ax.set_ylim( gymin, gymax )

def margin( ax, which="xy", size=0.025, ratio=1, logscale=False ):
    # xaxis
    if "x" in which:
        xmin, xmax = ax.get_xlim( )
        if logscale:
            xmin = log( xmin ) / log( 10 )
            xmax = log( xmax ) / log( 10 )
        xdiff = abs( xmax - xmin )
        xmin = xmin - xdiff * size
        xmax = xmax + xdiff * size 
        if logscale:
            xmin = 10**xmin
            xmax = 10**xmax
        ax.set_xlim( xmin, xmax )
    # yaxis
    if "y" in which:
        ymin, ymax = ax.get_ylim( )
        if logscale:
            ymin = log( ymin ) / log( 10 )
            ymax = log( ymax ) / log( 10 )
        ydiff = abs( ymax - ymin )
        ymin = ymin - ydiff * size
        ymax = ymax + ydiff * size
        if logscale:
            ymin = 10**ymin
            ymax = 10**ymax
        ax.set_ylim( ymin, ymax )

#-------------------------------------------------------------------------------
# working with text
#-------------------------------------------------------------------------------

def reltext( ax, x, y, text, **kwargs ):
    xmin, xmax = ax.get_xlim( )
    xdiff = abs( xmax - xmin )
    x = xmin + x * xdiff
    ymin, ymax = ax.get_ylim( )
    ydiff = abs( ymax - ymin )
    y = ymin + y * ydiff
    ax.text( x, y, text, **kwargs )
    
#-------------------------------------------------------------------------------
# itunes
#-------------------------------------------------------------------------------

def itunes_bars( ax, ref=None, width=1.0, color="0.95" ):
    hwidth = width / 2.0
    ymin, ymax = ax.get_ylim( )
    c = 0
    if ref is None:
        ref = ax.xaxis.get_majorticklocs( )
    for x in ref:
        c += 1
        if c % 2 == 1:
            ax.bar( x-hwidth, ymax-ymin, bottom=ymin,
                    width=width, color=color, edgecolor="none", zorder=0 )

def itunes_hbars( ax, ref=None, width=1.0, color="0.95" ):
    hwidth = width / 2.0
    xmin, xmax = ax.get_xlim( )
    c = 0
    if ref is None:
        ref = ax.yaxis.get_majorticklocs( ) 
    for y in ref:
        c += 1
        if c % 2 == 1:
            ax.barh( y-hwidth, xmax-xmin, left=xmin,
                     height=width, color=color, edgecolor="none", zorder=0 )

def ybands( ax, color="0.95" ):
    xmin, xmax = ax.get_xlim( )
    yy = ax.yaxis.get_majorticklocs( )
    i = 1
    while i + 1 < len( yy ):
        y1 = yy[i]
        y2 = yy[i+1]
        ax.barh( y1, xmax-xmin, left=xmin, height=y2 - y1,
                 color=color, edgecolor="none", zorder=0 )
        i += 2
        
#-------------------------------------------------------------------------------
# design a boxplot path
#-------------------------------------------------------------------------------

verts = [
    [-1.0, +0.0, mpl.path.Path.MOVETO],
    [-1.0, +0.6, mpl.path.Path.LINETO],
    [+1.0, +0.6, mpl.path.Path.LINETO],
    [+1.0, -0.6, mpl.path.Path.LINETO],
    [-1.0, -0.6, mpl.path.Path.LINETO],
    [-1.0, +0.0, mpl.path.Path.LINETO],
    [+1.0, +0.0, mpl.path.Path.LINETO],
    [+0.0, +0.6, mpl.path.Path.MOVETO],
    [+0.0, +1.2, mpl.path.Path.LINETO],
    [+0.0, -0.6, mpl.path.Path.MOVETO],
    [+0.0, -1.2, mpl.path.Path.LINETO],
]
codes = [k[-1]  for k in verts]
verts = [k[0:2] for k in verts]
boxplot_path = mpl.path.Path( verts, codes )

#-------------------------------------------------------------------------------
# legend
#-------------------------------------------------------------------------------

class Legendizer( ):

    def __init__( self, ax, vscale=2.0, magnify=1.0, offset=0, ):

        self.ax = ax
        self.spacing = 0.05 * vscale
        self.start = 0.5
        self.margin = 0.1 + offset
        self.textbuffer = 0.05
        self.magnify = magnify
        self.height = self.start
        self.delta = 0
        self.ax.set_ylim( 0, 1 )
        self.ax.set_xlim( 0, 1 )
        self.colortext = False
        self.commands = []

    def element( self, *args, **kwargs ):
        self.delta += 0.5 * self.spacing
        self.commands.append( ["element", args, kwargs] )
        
    def draw_element( self, marker="o", color="gray", edgecolor="black", size=50, label="N/A", labelsize=8 ):

        if "text:" in marker:
            self.ax.text( self.margin, self.height,
                          marker.replace( "text:", "" ),
                          va="center",
                          ha="center",
                          size=labelsize * self.magnify,
                          color=color,
                          weight="bold",
                          clip_on=False, )

        elif "line:" in marker:
            kwargs = {}
            for item in marker.split( ):
                if "=" in item:
                    k, v = item.split( "=" )
                    kwargs[k] = v            
            self.ax.add_line(
                plt.Line2D(
                    [self.margin * 0.75, self.margin * 1.25],
                    [self.height, self.height],
                    color=color,
                    clip_on=False,
                    **kwargs
                )
            )

        else:
            if marker == "boxplot":
                marker = boxplot_path
            self.ax.scatter(
                [self.margin], [self.height],
                marker=marker,
                s=size * self.magnify,
                color=color,
                edgecolor=edgecolor,
                clip_on=False,
            )
            # background?
            if color in ["white", "none"] and edgecolor in ["white", "none"]:
                self.ax.scatter( [self.margin], [self.height], marker="s",
                                 color="black", edgecolor="none",
                                 s=1.5 * size * self.magnify, zorder=0, )

        self.ax.text( self.margin + self.textbuffer,
                      self.height, label,
                      color="black" if not self.colortext else color,
                      va="center",
                      ha="left",
                      size=labelsize * self.magnify,
                      clip_on=False, )

        self.height -= self.spacing

    def subhead( self, *args, **kwargs ):
        self.skip( )
        self.delta += 0.5 * self.spacing
        self.commands.append( ["subhead", args, kwargs] )                          

    def draw_subhead( self, text, labelsize=10, ):
        self.ax.text( self.margin + self.textbuffer,
                      self.height,
                      text,
                      va="center", ha="left",
                      size=labelsize * self.magnify,
                      weight="bold", )
        self.height -= self.spacing

    def skip( self, *args, **kwargs ):
        self.delta += 0.5 * 0.5 * self.spacing
        self.commands.append( ["skip", args, kwargs] )
                                  
    def draw_skip( self ):
        self.height -= self.spacing / 2.0

    def color_guide( self, mapping, order=None, title="Colors" ):
        self.subhead( title )
        if order is None:
            order = sorted( mapping )
        for name in order:
            self.element( marker="s", color=mapping[name], label=name )
        
    def draw( self ):
        self.height += self.delta
        for name, args, kwargs in self.commands:
            if name == "element":
                self.draw_element( *args, **kwargs )
            elif name == "subhead":
                self.draw_subhead( *args, **kwargs )
            elif name == "skip":
                self.draw_skip( *args, **kwargs )
                
#-------------------------------------------------------------------------------
# indexing
#-------------------------------------------------------------------------------

def limdex( batches, sep=1.0, margin=1.0, width=0.0 ):
    x = 0
    lims = [x]
    half = width / 2.0
    ticks = []
    if type( batches ) is int:
        batches = [batches]
    for b in batches:
        x += margin
        for i in range( b ):
            x += half if i == 0 else sep
            ticks.append( x )
        x += half
    x += margin
    lims.append( x )
    return lims, ticks
    
def index1( ax, groups, width=1.0, xaxis=True, bardex=False ): 
    """ Prepares an axes for plotting one column per sample """
    index = range( 0, groups )
    hfwidth = width / 2.0
    margin = 1 - width
    kmin = index[0] - hfwidth - margin
    kmax = index[-1] + hfwidth + margin
    if xaxis:
        #ax.set_xticks( index )
        ax.set_xlim( kmin, kmax )
    else:
        #ax.set_yticks( index )
        ax.set_ylim( kmin, kmax )
    if bardex:
        index = [k - hfwidth for k in index]
    return index

def index2( ax, groups, series, width=0.9, spacing=0, bardex=False ):
    """ Prepares an axes for plotting multiple columns per sample """
    index = [range( 0, groups )]
    margin = 1 - width
    xmin = width / 2.0 - margin
    xmax = index[-1] + width / 2.0 + margin
    ax.set_xlim( xmin, xmax )
    sspace = spacing * width / float( series - 1 )
    swidth = (width - sspace * (series - 1)) / float( groups )
    index2 = [[] for k in index]
    for a, start in zip( index2, index ):
        for s in range( series ):
            a.append( start - width / 2.0 + swidth / 2.0 + s * (swidth + sspace) )
            if bardex:
                a[-1] -= swidth / 2.0
    return index, index2

# ---------------------------------------------------------------
# line drawing
# ---------------------------------------------------------------

def vintercept( intercept, slope, x ):
    return intercept + x * slope

def hintercept( intercept, slope, y ):
    return ( y - intercept ) / float( slope )

def abline( ax, intercept, slope, **kwargs ):
    """ draws a line in the axes through the intercept with slope """
    # get limits
    xmin, xmax = ax.get_xlim( )
    ymin, ymax = ax.get_ylim( )
    # line should originate at yaxis
    xminline_intercept = vintercept( intercept, slope, xmin )
    xmaxline_intercept = vintercept( intercept, slope, xmax )
    yminline_intercept = hintercept( intercept, slope, ymin )
    ymaxline_intercept = hintercept( intercept, slope, ymax )
    points = []
    # only two of these can be true ( line must pass through 2 of 4 bounding edges )
    if ymin <= xminline_intercept <= ymax:
        points.append( ( xmin, xminline_intercept ) )
    if xmin <= yminline_intercept <= xmax:
        points.append( ( yminline_intercept, ymin ) )
    if ymin <= xmaxline_intercept <= ymax:
        points.append( ( xmax, xmaxline_intercept ) )
    if xmin <= ymaxline_intercept <= xmax:
        points.append( ( ymaxline_intercept, ymax ) )
    # draw the line
    xvals = [ k[0] for k in points ]
    yvals = [ k[1] for k in points ]
    ax.plot( xvals, yvals, **kwargs )

def hline( ax, y, **kwargs ):
    xmin, xmax = ax.get_xlim()
    ax.add_line( plt.Line2D( [xmin, xmax], [y, y], **kwargs ) )

def vline( ax, x, **kwargs ):
    ymin, ymax = ax.get_ylim()
    ax.add_line( plt.Line2D( [x, x], [ymin, ymax], **kwargs ) )

#-------------------------------------------------------------------------------
# barplot
#-------------------------------------------------------------------------------
    
def barplot( ax, data, labels=None, ticks=None, yerr=None, colors=None, width=0.9 ):
    if ticks is None:
        lims, ticks = limdex( len( data ), width=width )    
    for i, x in enumerate( ticks ):
        kwargs = {}
        kwargs["edgecolor"] = "none"
        kwargs["color"] = colors[i] if colors is not None else c_dcolor
        if yerr is not None:
            kwargs["yerr"] = yerr[i]
            kwargs["ecolor"] = "black"
        ax.bar( x - width / 2.0, data[i], width=width, **kwargs )
    if labels is not None:
        ax.set_xticklabels( labels, rotation_mode="anchor", ha="right", rotation=35 )

#-------------------------------------------------------------------------------
# histogram
#-------------------------------------------------------------------------------

def hist( ax, values, ulimits, leftover=None, show_counts=False ):
    """ makes a histogram """
    if leftover is not None:
        ulimits.append( leftover )
    index = index1( ax, len( ulimits ), bardex=True, width=1.0 )
    hcounts = Counter( )
    for v in values:
        for xbin in ulimits:
            if leftover is not None and xbin == leftover:
                hcounts[xbin] += 1
                break
            elif v <= xbin:
                hcounts[xbin] += 1
                break
    heights = [hcounts[xbin] / float( len( values ) ) for xbin in ulimits]
    for i in range( len( index ) ):
        ax.bar( index[i], heights[i], width=1.0, color=c_dcolor, edgecolor="none" )
        if show_counts:
            ax.text( 
                0.5 + index[i], 
                heights[i] + 0.1,
                str( hcounts[ulimits[i]] ),
                size=9,
                ha="center",
                va="center",
                color="0.5",
            )
    ax.set_xticks( [k + 0.5 for k in index] )
    ax.set_xticklabels( ulimits )
    ax.set_yticks( [0, 0.25, 0.50, 0.75, 1.0] )
    ax.set_ylabel( "Frequency" )

#-------------------------------------------------------------------------------
# scatter
#-------------------------------------------------------------------------------

def logminmax( data ):
    """ for determining log plotting limits; data can be 1 or 2 dimensional """
    if isinstance( data[0], list ):
        data2 = []
        for row in data:
            data2 += row
        data = data2
    data2 = [k for k in data if k != 0 and k is not None]
    if len( data2 ) != len( data ):
        print >>sys.stderr, "ATTENTION ( LogMinMax ):", len( data ) - len( data2 ), "Zero|NA values not considered"
    data = data2
    tempMin = min( data )
    tempMax = max( data ) 
    return 10**floor( log( tempMin, 10 ) ), 10**ceil( log( tempMax, 10 ) )

# DEPRECATE?
def vkwargs( n, **kwargs ):
    """ converts all arguments to vectors, e.g. color="blue" becomes color=["blue", "blue", "blue", ...]"""
    for key, value in kwargs.items():
        if not isinstance( value, list ):
            kwargs[key] = [value for i in range( n )]
    return kwargs

# DEPRECATE?
def scatter( ax, xvals, yvals, **kwargs ):
    """
    kwargs can be scalar or vectors of things the mpl scatter understands, e.g. color
    scalars are exploded into vectors
    points are then plotted individually
    """
    # coerce scalar values to vectors
    kwargs = vkwargs( len( xvals ), **kwargs )
    # check that all vectors have the same length
    lens = [len( xvals )] + [len( yvals )] + [len( vals ) for vals in kwargs.values()]
    if len( set( aLengths ) ) != 1:
        sys.exit( "EXITING: scatter called with vectors of unequal length" )
    # else, plot points ( check boundaries )
    for i in range( len( xvals ) ):
        if len( xvals ) > 1000 and i % 1000 == 0:
            print >>sys.stderr, "ATTENTION ( Scatter ):", "Plotting lots of points, progress =", "%d%%" % ( 100 * i / float( len( xvals ) ) )
        if not funcWithin( xvals[i], ax.get_xlim() ) or not funcWithin( yvals[i], ax.get_ylim() ):
            print >>sys.stderr, "ATTENTION ( Scatter ):", "point", xvals[i], yvals[i], "not within", ax.get_xlim(), ax.get_ylim()
        ax.scatter( [xvals[i]], [yvals[i]], **{key:aValues[i] for key, aValues in kwargs.items()} )
        if "label" in kwargs:
            ax.text( xvals[i], yvals[i], kwargs["label"][i] )

#-------------------------------------------------------------------------------
# swarm
#-------------------------------------------------------------------------------

def spaced( vv, windows=25, width=1.0 ):
    a = min( vv )
    b = max( vv )
    f = b - a
    d = f / float( windows )
    ww = {}
    for i, v in enumerate( vv ):
        for w in range( windows + 1 ):
            if v <= a + d * w:
                ww.setdefault( w, [] ).append( i )
                break
    jj = [0 for v in vv]
    for wset in ww.values( ):
        n = len( wset )
        if n > 1:
            for i, x in enumerate( wset ):
                jj[x] = -0.5 * width + width * (i + 1) / float( n + 1 )
    return jj

def jitters( vv, windows=25, width=1.0 ):
    a = min( vv )
    b = max( vv )
    f = b - a
    d = f / float( windows )
    ww = [0 for k in vv]
    for i, v in enumerate( vv ):
        for w in range( windows + 1 ):
            if v <= a + d * w:
                ww[i] = w
                break
    cc = Counter( ww )
    jj = [cc[w] - 1 for w in ww]
    jj = [j / max( jj ) for j in jj]
    jj = [j * (-0.5 * width + random( ) * width) for j in jj]
    return jj

def density( vv, step=0.05 ):
    e = max( vv ) - min( vv )
    e *= step
    dd = []
    for v in vv:
        dd.append( len( [k for k in vv if (v-e <= k <= v+e)] ) - 1 )
    s = float( max( dd ) )
    # when each window is a singleton
    s = 1 if s == 0 else s 
    dd = [k/s for k in dd]
    return dd

def swarm( ax, labels=None, values=None, data=None, order=None, colors=None,
           width=0.9, vert=True, fast=False,
           alpha=0.5, s=20, no_label=False ):
    data = shatter( labels, values ) if data is None else data
    labels = sorted( data ) if order is None else order
    index = index1( ax, len( data ), xaxis=vert, width=width )
    if colors is None:
        colors = {l:c_dcolor for l in labels}
    for coord, label in zip( index, labels ):
        vv = data[label]
        dd = density( vv ) if not fast else [1 for k in vv]
        for v, d in zip( vv, dd ):
            y = v
            x = coord + (random( ) - 0.5) * width * d
            if not vert:
                y, x = x, y
            ax.scatter( [x], [y],
                        color=colors[label],
                        edgecolor="none",
                        alpha=alpha,
                        s=s,
            )
    if not no_label:
        if vert:
            ax.set_xticklabels( labels, rotation_mode="anchor", ha="right", rotation=35 )
        else:
            ax.set_yticklabels( labels )
        
#-------------------------------------------------------------------------------
# boxplot
#-------------------------------------------------------------------------------

def boxplot(

        ax,
        labels=None,
        values=None,
        data=None,
        min_points=1,
        width=0.9,
        vert=True,
        colors=None,
        face_colors=None,
        order=None,
        groups=None,
        outliers=None,
        outliersize=5,
        label_angle=35,
        positions=None,

):

    data = data if data is not None else shatter( labels, values )
    labels = sorted( data ) if order is None else order
    labels2 = [labels[k/2] for k in range( 2 * len( labels ) )]
    data = [data[k] for k in labels]
    if positions is None:
        lims, positions = limdex( len( data ), width=width )
    if not colors:
        colors = {l:"black" for l in labels}
    if not face_colors:
        face_colors = {l:"none" for l in labels}
    # hide plots with few points
    for l, dd in zip( labels, data ):
        if len( dd ) < min_points:
            colors[l] = "none"
            face_colors[l] = "none"
    # boxplots
    bp = ax.boxplot( 
        data,
        notch=False,
        sym=".",
        vert=vert,
        patch_artist=True,
        widths=width,
        positions=positions,
        whis="range" if outliers is None else 1.5,
    )
    # box properties
    for l, box, median in zip( labels, bp["boxes"], bp["medians"] ):
        box.set( color=colors[l] )
        box.set( facecolor=face_colors[l] )
        median.set( color=colors[l] )
    # whisker properties (2x)
    for l, whisker in zip( labels2, bp["whiskers"] ):
        whisker.set( color=colors[l], linestyle="-" )
    # cap properties (just hide)
    for cap in bp["caps"]:
        cap.set( visible=False )
    # "flier" properties
    for l, f in zip( labels, bp["fliers"] ):
        if outliers is None:
            pass
        elif outliers == "hide":
            f.set_visible( False )
        elif outliers == "face":
            f.set_markerfacecolor( face_colors[l] )
            f.set_markeredgecolor( "none" )
            f.set_markersize( outliersize )
        elif outliers == "edge":
            f.set_markerfacecolor( colors[l] )
            f.set_markeredgecolor( "none" )
            f.set_markersize( outliersize )
    # set verticle
    if vert:
        ax.set_xticks( positions )
        if label_angle > 0 and max( [len( str( k ) ) for k in labels] ) > 3:
            ax.set_xticklabels( labels, rotation_mode="anchor", ha="right", va="center", rotation=label_angle )
        else:
            ax.set_xticklabels( labels )
    else:
        ax.set_yticks( positions )
        ax.set_yticklabels( labels )
