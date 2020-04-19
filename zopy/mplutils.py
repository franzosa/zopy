#! /usr/bin/env python

import os, sys, re, glob, argparse
from collections import Counter
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from random import random
from math import floor, ceil, log

# ---------------------------------------------------------------
# constants
# ---------------------------------------------------------------

c_fGroupWidth = 0.9

# ---------------------------------------------------------------
# building axis systems
# ---------------------------------------------------------------

"""
Creates a grid of plots with the specified dimensions
Ex. aaAxes = funcPlotMatrix( [4,2,2,1], [2,1] ) makes

111122334
111122334
555566778

where each "#" indicates a plotting area; easier than
the subplot2grid syntax for simple plots.
"""

def funcPlotMatrix ( aWidths, aHeights ):
    aaPlots = []
    rmax = sum( aHeights )
    cmax = sum( aWidths )
    rdex = 0
    for i, height in enumerate( aHeights ):
        aRow = []
        cdex = 0
        for j, width in enumerate( aWidths ):
            aRow.append( 
                plt.subplot2grid( 
                   ( rmax, cmax ), 
                    ( rdex, cdex ), 
                    rowspan=aHeights[i], 
                    colspan=aWidths[j], 
                ) 
            )
            cdex += aWidths[j]
        aaPlots.append( aRow )
        rdex += aHeights[i]
    return aaPlots

# ---------------------------------------------------------------
# axes style configuration
# ---------------------------------------------------------------

def funcSetTickParams ( axes, **kwargs ):
    """ Converts ticks from default matplotlib to default eric style """
    # major minor x
    axes.tick_params( axis="x", which="major", direction="out", bottom="on", top="off", width=1.0, **kwargs )
    axes.tick_params( axis="x", which="minor", direction="out", bottom="on", top="off", width=1.0, **kwargs )
    # major minor y
    axes.tick_params( axis="y", which="major", direction="out", left="on", right="off", width=1.0, **kwargs )
    axes.tick_params( axis="y", which="minor", direction="out", left="on", right="off", width=1.0, **kwargs )

def funcHideTicks ( axes, x=True, y=True ):
    if x:
        for t in axes.xaxis.get_major_ticks(): 
            t.tick1On = False 
            t.tick2On = False
    if y:
        for t in axes.yaxis.get_major_ticks(): 
            t.tick1On = False
            t.tick2On = False

def funcHideX ( axes, major=True, minor=True ):
    """ Hides all x axis elements """
    if major:
        [ label.set_visible( False ) for label in axes.get_xticklabels() ]
        [ tick.set_visible( False )  for tick  in axes.xaxis.get_major_ticks() ]
    if minor:
        [ tick.set_visible( False )  for tick  in axes.xaxis.get_minor_ticks() ]

def funcHideY ( axes, major=True, minor=True ):
    """ Hides all y axis elements """
    if major:
        [ label.set_visible( False ) for label in axes.get_yticklabels() ]
        [ tick.set_visible( False )  for tick  in axes.yaxis.get_major_ticks() ]
    if minor:
        [ tick.set_visible( False )  for tick  in axes.yaxis.get_minor_ticks() ]

def funcBorder ( axes, **kwargs ):
    """ apply general properties to the border """
    plt.setp( [child for child in axes.get_children() if isinstance( child, mpl.spines.Spine )], **kwargs )

def funcHideBorder( axes ):
    """ hides the border of a plot; surprisingly tricky """
    plt.setp( [child for child in axes.get_children() if isinstance( child, mpl.spines.Spine )], visible=False )

def funcDummyPlot( axes ):
    """ leaves an empty plot in a grid """
    funcHideX( axes )
    funcHideY( axes )
    funcHideBorder( axes )

def funcGrid ( axes, xaxis=True, yaxis=True, xy=False, minor=False, color="0.95", linestyle="-", zorder=0, **kwargs ):
    """ Makes a grid that doesn't depend on x,y visibility """
    # embed extra options in kwargs
    kwargs["color"] = color
    kwargs["linestyle"] = linestyle
    kwargs["zorder"] = zorder
    aX = axes.xaxis.get_majorticklocs()[1:] if not minor else axes.xaxis.get_minorticklocs()
    aY = axes.yaxis.get_majorticklocs()[1:] if not minor else axes.yaxis.get_minorticklocs()
    xmin, xmax = axes.get_xlim()
    ymin, ymax = axes.get_ylim()
    if xaxis:
        for x in aX:
            axes.add_line( plt.Line2D( [x, x], [ymin, ymax], **kwargs ) )
    if yaxis:
        for y in aY:
            axes.add_line( plt.Line2D( [xmin, xmax], [y, y], **kwargs ) )
    if xy:
        minmin = min( xmin, ymin )
        minmax = min( xmax, ymax )
        axes.add_line( plt.Line2D( [minmin, minmax], [minmin, minmax], **kwargs ) )

def funcGrid2( ax, h=None, v=None, border=False, color="0.95", zorder=0, **kwargs ):
    xmin, xmax = ax.get_xlim()
    ymin, ymax = ax.get_ylim()
    # embed extra options in kwargs
    kwargs["color"] = color
    kwargs["zorder"] = zorder
    if h is not None:
        for y in h:
            ax.add_line( plt.Line2D( [xmin, xmax], [y, y], **kwargs ) )
    if v is not None:
        for x in v:
            ax.add_line( plt.Line2D( [x, x], [ymin, ymax], **kwargs ) )
    if border:
        funcBorder( ax, **kwargs )
        
def funcPercentLabels( ax, xaxis=True, yaxis=True ):
    if xaxis: ax.set_xticklabels( ["%d" % ( 100 * k ) for k in ax.get_xticks()] )
    if yaxis: ax.set_yticklabels( ["%d" % ( 100 * k ) for k in ax.get_yticks()] )

def funcTitleBox( ax, scale=0.1 ):
    """ hack for getting boxes around titles """
    x1, y1, x2, y2 = [float( x ) for x in re.sub( "[^\-0-9\.\,]", "", ax.get_position().__repr__() ).split( "," )]
    dx = x2 - x1
    dy = y2 - y1
    # this needs access to the "fig" object
    ax2 = plt.gcf().add_axes( [x1, y2, dx, dy * scale] )
    ax2.set_axis_bgcolor( "0.9" )
    funcHideX( ax2 )
    funcHideY( ax2 )
    ax2.text( 
        0.5, 
        0.5, 
        ax.title.get_text(),
        ha="center", 
        va="center",
        style=ax.title.get_style(),
        color=ax.title.get_color(),
        size=ax.title.get_size(),
        weight=ax.title.get_weight(),
    )
    ax.set_title( "" )

# ---------------------------------------------------------------
# aaAxes operations
# ---------------------------------------------------------------

def funcIterAxes( aaAxes ):
    """ generator """
    for axrow in aaAxes:
        for ax in axrow:
            yield ax

def funcApplyAxes ( aaAxes, function, **kwargs ):
    """ applies a function to a bunch of axes """
    for ax in funcIterAxes( aaAxes ):
        function( ax, **kwargs )

def funcHideInnerAxes ( aaAxes, simplify=False ):
    """ only show the outer grid axes """
    for i, axrow in enumerate( aaAxes ):
        for j, ax in enumerate( axrow ):
            if i+1 < len( aaAxes ):
                funcHideX( ax )
                ax.set_xlabel( "" )
            if j > 0:
                funcHideY( ax )
                ax.set_ylabel( "" )
            if simplify and ( i+1 < len( aaAxes ) or j != 0 ):
                # only label axes at the bottom left corner
                ax.set_xlabel( "" )
                ax.set_ylabel( "" )

def funcCommonLimits ( aaAxes, forcex=True, forcey=True ):
    """ enforce common mins and maxes """
    # get
    gxmin, gxmax, gymin, gymax = None, None, None, None
    for ax in funcIterAxes( aaAxes ):
        xmin, xmax = ax.get_xlim()
        gxmin = xmin if gxmin is None or xmin < gxmin else gxmin
        gxmax = xmax if gxmax is None or xmax > gxmax else gxmax
        ymin, ymax = ax.get_ylim()
        gymin = ymin if gymin is None or ymin < gymin else gymin
        gymax = ymax if gymax is None or ymax > gymax else gymax
    # set
    for ax in funcIterAxes( aaAxes ):
        if forcex:
            ax.set_xlim( gxmin, gxmax )
        if forcey:
            ax.set_ylim( gymin, gymax )

def funcMargin( ax, size=0.05 ):
    # xaxis
    xmin, xmax = ax.get_xlim()
    xdiff = xmax - xmin
    ax.set_xlim( xmin - xdiff * size, xmax + xdiff * size )
    # yaxis
    ymin, ymax = ax.get_ylim()
    ydiff = ymax - ymin
    ax.set_ylim( ymin - ydiff * size, ymax + ydiff * size )

# ---------------------------------------------------------------
# whole-axis legend
# ---------------------------------------------------------------

def funcAddLegend( axes, elements, start=0.9, spacing=0.1, 
                   margin=0.1, textbuffer=0.1, labelsize=8 ):
    """ 
    elements will be scattered 
    each has structure ( marker, color, edgecolor, size, text )
    if marker like "--TEXT--", will plot TEXT as the marker
    """
    axes.set_xlim( 0, 1 )
    axes.set_ylim( 0, 1 )
    funcHideX( axes )
    funcHideY( axes )
    funcHideBorder( axes )
    height = start
    for ( marker, color, edgecolor, size, label ) in elements:
        match = re.search( "--(.*)--", marker )
        if match:
            axes.text( margin, height, match.group( 1 ), va="center", ha="center", size=labelsize, color=color, weight="bold" )
        else:
            axes.scatter( [margin], [height], marker=marker, s=size, color=color, edgecolor=edgecolor )
        axes.text( margin + textbuffer, height, label, va="center", ha="left", size=labelsize, clip_on=False )
        height -= spacing

class Legendizer( ):
    def __init__( self, ax ):
        self.ax = ax
        self.start = 0.95
        self.spacing = 0.05
        self.margin = 0.1
        self.textbuffer = 0.1
        self.labelsize = 8
        self.height = self.start
        self.ax.set_ylim( 0, 1 )
        self.ax.set_xlim( 0, 1 )
        funcDummyPlot( ax )
    def add_element( self, marker="o", color="white", edgecolor="black", size=10, label="NO_LABEL" ):
        if "text:" in marker:
            self.ax.text( self.margin, self.height,
                          marker.replace( "text:", "" ),
                          va="center", ha="center",
                          size=self.labelsize,
                          color=color, weight="bold", )
        else:
            self.ax.scatter( [self.margin], [self.height],
                          marker=marker, s=size,
                          color=color, edgecolor=edgecolor, )
        self.ax.text( self.margin + self.textbuffer,
                      self.height, label,
                      va="center", ha="left",
                      size=self.labelsize, clip_on=False )
        self.height -= self.spacing
    def add_subhead( self, text ):
        self.ax.text( 0.5 * self.margin, self.height,
                      text,
                      va="center", ha="left",
                      size=self.labelsize * 1.2,
                      weight="bold", )
        self.height -= self.spacing
        
# ---------------------------------------------------------------
# x-axis indexing for barplots, etc.
# ---------------------------------------------------------------

def funcGroupIndex ( axes, nGroups, width=c_fGroupWidth ):
    """ Prepares an axes for plotting one column per sample """
    aIndex = np.arange( nGroups ) + 1
    xMin = width / 2.0
    xMax = aIndex[-1] + 1 - width / 2.0
    axes.set_xlim( xMin, xMax )
    return aIndex

def funcSeriesIndex ( axes, nGroups, nSeries, width=c_fGroupWidth ):
    """ Prepares an axes for plotting multiple columns per sample """
    width2 = width / float( nSeries )
    aGroupIndex = np.arange( nGroups ) + 1
    aaSeriesIndex = []
    for i, groupCenter in enumerate( aGroupIndex ):
        seriesStart = groupCenter - width2 * ( nSeries - 1 ) / 2.0
        aSeries = [ seriesStart + k * width2 for k in range( nSeries ) ]
        aaSeriesIndex.append( aSeries )
    xMin = width / 2.0
    xMax = aGroupIndex[-1] + 1 - width / 2.0
    axes.set_xlim( xMin, xMax )
    return aGroupIndex, aaSeriesIndex

# ---------------------------------------------------------------
# line drawing
# ---------------------------------------------------------------

def funcInterceptV ( intercept, slope, x ):
    return intercept + x * slope

def funcInterceptH ( intercept, slope, y ):
    return ( y - intercept ) / float( slope )

def funcABline ( axes, intercept, slope, **kwargs ):
    """ draws a line in the axes through the intercept with slope """
    # get limits
    xmin, xmax = axes.get_xlim()
    ymin, ymax = axes.get_ylim()
    # line should originate at yaxis
    xminline_intercept = funcInterceptV( intercept, slope, xmin )
    xmaxline_intercept = funcInterceptV( intercept, slope, xmax )
    yminline_intercept = funcInterceptH( intercept, slope, ymin )
    ymaxline_intercept = funcInterceptV( intercept, slope, ymax )
    aPoints = []
    # only two of these can be true ( line must pass through 2 of 4 bounding edges )
    if ymin < xminline_intercept < ymax:
        aPoints.append( ( xmin, xminline_intercept ) )
    if xmin < yminline_intercept < xmax:
        aPoints.append( ( yminline_intercept, ymin ) )
    if ymin < xmaxline_intercept < ymax:
        aPoints.append( ( xmax, xmaxline_intercept ) )
    if xmin < ymaxline_intercept < xmax:
        aPoints.append( ( ymaxline_intercept, ymax ) )
    # draw the line
    aXvals = [ k[0] for k in aPoints ]
    aYvals = [ k[1] for k in aPoints ]
    axes.add_line( plt.Line2D( aXvals, aYvals, **kwargs ) )

def funcHline( ax, y, **kwargs ):
    xmin, xmax = ax.get_xlim()
    ax.add_line( plt.Line2D( [xmin, xmax], [y, y], **kwargs ) )

def funcVline( ax, x, **kwargs ):
    ymin, ymax = ax.get_ylim()
    ax.add_line( plt.Line2D( [x, x], [ymin, ymax], **kwargs ) )
    
# ---------------------------------------------------------------
# functions for making bar plots
# ---------------------------------------------------------------

def funcBar ( axes, center, value, width=c_fGroupWidth, nSeries=1, **kwargs ):
    width /= float( nSeries )
    axes.bar( center - width / 2.0, value, width=width, **kwargs )

def funcBarPlot ( ax, aData, labels=None, yerr=None ):
    """ """
    aIndex = funcGroupIndex( ax, len( aData ) )
    for i, value in enumerate( aIndex ):
        kwargs = { "edgecolor":"none" }
        if yerr is not None:
            kwargs["yerr"] = yerr[i]
            kwargs["ecolor"] = "black"
        funcBar( ax, aIndex[i], aData[i], color="cornflowerblue", **kwargs )
    if labels is not None:
        ax.set_xticklabels( labels, rotation_mode="anchor", ha="right", rotation=35 )

# ---------------------------------------------------------------
# simple swarm plot
# ---------------------------------------------------------------

def funcSwarm( ax, aaData, labels=None ):
    # data is 2d, d1 is categories
    aIndex = funcGroupIndex( ax, len( aaData ) )
    for x, aValues in zip( aIndex, aaData ):
        for v in aValues:
            vy = v
            vx = x + ( random() - 0.5 ) * 0.8
            ax.scatter( [vx], [vy], color="cornflowerblue", edgecolor="none", alpha=0.5 )
    if labels is not None:
        ax.set_xticklabels( labels, rotation_mode="anchor", ha="right", rotation=35 )

# ---------------------------------------------------------------
# simple histogram
# ---------------------------------------------------------------

def funcHist( ax, aValues, aBinUpperLimits, leftover=None, label=False ):
    """ makes a histogram """
    if leftover is not None:
        aBinUpperLimits.append( leftover )
    aIndex = funcGroupIndex( ax, len( aBinUpperLimits ) )
    dictHistCounter = Counter()
    for value in aValues:
        for xbin in aBinUpperLimits:
            if leftover is not None and xbin == leftover:
                dictHistCounter[xbin] += 1
                break
            elif value <= xbin:
                dictHistCounter[xbin] += 1
                break
    aHeights = [dictHistCounter[xbin] / float( len( aValues ) ) for xbin in aBinUpperLimits]
    for i in range( len( aIndex ) ):
        ax.bar( aIndex[i]-0.45, aHeights[i], width=0.9, color="royalblue", edgecolor="none" )
        if label:
            ax.text( 
                aIndex[i], aHeights[i] + 0.1,
                str( dictHistCounter[aBinUpperLimits[i]] ),
                size=9,
                ha="center",
                va="center",
                color="0.5",
            )
    ax.set_xticks( aIndex )
    ax.set_xticklabels( aBinUpperLimits )
    ax.set_yticks( [0, 0.25, 0.50, 0.75, 1.0] )
    funcPercentLabels( ax, xaxis=False )

#-------------------------------------------------------------------------------
# boxplots
#-------------------------------------------------------------------------------
    
# ---------------------------------------------------------------
# special scatter options
# ---------------------------------------------------------------

def funcLogMinMax ( data ):
    """ for determining log plotting limits; data can be 1 or 2 dimensional """
    if isinstance ( data[0], list ):
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

def funcVectorizeKwargs ( n, **kwargs ):
    """ converts all arguments to vectors, e.g. color="blue" becomes color=["blue", "blue", "blue", ...]"""
    for key, value in kwargs.items():
        if not isinstance( value, list ):
            kwargs[key] = [value for i in range( n )]
    return kwargs

def funcWithin ( coord, aLimits ):
    """ tests if a point is being plotted outside the plot area """
    return True if aLimits[0] <= coord <= aLimits[1] else False

def funcScatter ( ax, aX, aY, **kwargs ):
    """
    kwargs can be scalar or vectors of things the mpl scatter understands, e.g. color
    scalars are exploded into vectors
    points are then plotted individually
    """
    # coerce scalar values to vectors
    kwargs = funcVectorizeKwargs( len( aX ), **kwargs )
    # check that all vectors have the same length
    aLengths = [len( aX )] + [len( aY )] + [len( aValues ) for aValues in kwargs.values()]
    if len( set( aLengths ) ) != 1:
        sys.exit( "EXITING: funcScatter called with vectors of unequal length" )
    # else, plot points ( check boundaries )
    for i in range( len( aX ) ):
        if len( aX ) > 1000 and i % 1000 == 0:
            print >>sys.stderr, "ATTENTION ( Scatter ):", "Plotting lots of points, progress =", "%d%%" % ( 100 * i / float( len( aX ) ) )
        if not funcWithin( aX[i], ax.get_xlim() ) or not funcWithin( aY[i], ax.get_ylim() ):
            print >>sys.stderr, "ATTENTION ( Scatter ):", "point", aX[i], aY[i], "not within", ax.get_xlim(), ax.get_ylim()
        ax.scatter( [aX[i]], [aY[i]], **{key:aValues[i] for key, aValues in kwargs.items()} )
        if "label" in kwargs:
            ax.text( aX[i], aY[i], kwargs["label"][i] )

# ---------------------------------------------------------------
# working with color
# ---------------------------------------------------------------

def ncolors( n, colormap="jet" ):
    """utility for defining N evenly spaced colors across a color map"""
    cmap = plt.get_cmap( colormap )
    cmap_max = cmap.N
    if n > 1:
        return [cmap( int( k * cmap_max / (n - 1) ) ) for k in range( n )]
    else:
        return [cmap( 0.5 )]
    
# ---------------------------------------------------------------
# testing
# ---------------------------------------------------------------    

if __name__ == "__main__":  
    fig = plt.figure()
    axes = plt.subplot( 111 )
    plt.show()
