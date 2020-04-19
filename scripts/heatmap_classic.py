#!/usr/bin/env python

import os
import sys
import re
import argparse
import random
from collections import Counter

import matplotlib as mpl
mpl.use( "Agg" )
mpl.rcParams["pdf.fonttype"] = 42
mpl.rcParams["font.sans-serif"] = "Arial"
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pylab
import numpy as np
from scipy.stats import rankdata
import scipy.cluster.hierarchy as sch

from zopy.table2 import table
from zopy.utils import die, warn, path2name
import zopy.mplutils2 as mu
from zopy.dictation import col2dict, col2dict2

#-------------------------------------------------------------------------------
# constants
#-------------------------------------------------------------------------------

c_max_lab     = 50
c_metacmap    = "Dark2"
c_font1       = 7
c_font2       = 8
c_font3       = 10
c_eps         = 1e-20
c_str_other   = "Other"
c_str_none    = "None"
c_other_color = "0.75"
c_none_color  = "white"

sys.setrecursionlimit( 10000 )

#-------------------------------------------------------------------------------
# cli
#-------------------------------------------------------------------------------

def get_args( ):
    parser = argparse.ArgumentParser( )
    parser.add_argument( "table", help="" )
    parser.add_argument( "--lastcol",
                         help="" )
    parser.add_argument( "--lastrow",
                         help="" )
    parser.add_argument( "--colmeta",
                         nargs="+",
                         help="" )
    parser.add_argument( "--colmeta-colors",
                         nargs="+",
                         help="" )
    parser.add_argument( "--rowmeta",
                         nargs="+",
                         help="" )
    parser.add_argument( "--rowmeta-colors",
                         nargs="+",
                         help="" )
    parser.add_argument( "--max-levels",
                         type=int,
                         help="" )
    parser.add_argument( "--colsort",
                         default=["none"],
                         nargs="+",
                         help="" )
    parser.add_argument( "--rowsort",
                         default=["none"],
                         nargs="+",
                         help="" )
    parser.add_argument( "--dump-colsort-order",
                         action="store_true",
                         help="" )
    parser.add_argument( "--dump-rowsort-order",
                         action="store_true",
                         help="" )
    parser.add_argument( "--cmap",
                         default="inferno",
                         help="" )
    parser.add_argument( "--transform",
                         choices=["none", "sqrt", "log2", "log10"],
                         default="none",
                         help="" )
    parser.add_argument( "--limits",
                         nargs="+",
                         type=float,
                         help="" )
    parser.add_argument( "--units",
                         default="units",
                         help="" )
    parser.add_argument( "--rowlabel",
                         default="rows",
                         help="")
    parser.add_argument( "--collabel",
                         default="cols",
                         help="" )
    parser.add_argument( "--override-rownames",
                         default=None,
                         help="")
    parser.add_argument( "--override-colnames",
                         default=None,
                         help="" )
    parser.add_argument( "--debug",
                         action="store_true", help="" )
    parser.add_argument( "--hscale",
                         action="store_true",
                         help="" )
    parser.add_argument( "--vscale",
                         action="store_true",
                         help="" )
    parser.add_argument( "--hstretch",
                         type=float,
                         default=1.0,
                         help="" )
    parser.add_argument( "--vstretch",
                         type=float,
                         default=1.0,
                         help="" )
    parser.add_argument( "--legend-scale",
                         type=float,
                         default=1.0,
                         help="" )
    parser.add_argument( "--metascale",
                         action="store_true",
                         help="" )
    parser.add_argument( "--grid",
                         default="", # x y or xy
                         help="")
    parser.add_argument( "--rowbreaks",
                         help="")
    parser.add_argument( "--colbreaks",
                         help="" )
    parser.add_argument( "--break-color",
                         default="white",
                         help="" )
    parser.add_argument( "--linkage",
                         default="average",
                         help="" )
    parser.add_argument( "--engine",
                         choices=["imshow", "pcolormesh", "pcolorfast"],
                         default="imshow",
                         help="" )
    parser.add_argument( "--output",
                         default="heatmap.pdf",
                         help="" )
    parser.add_argument( "--overrides",
                         nargs="+",
                         default=[],
                         help="" )
    parser.add_argument( "--eps-noise",
                         action="store_true",
                         help="" )
    parser.add_argument( "--cbar-extent",
                         default=0.5,
                         type=float,
                         help="" )
    parser.add_argument( "--grid-inches",
                         default=0.25,
                         type=float,
                         help="" )
    parser.add_argument( "--title",
                         help="" )
    parser.add_argument( "--force-labels",
                         action="store_true",
                         help="" )
    parser.add_argument( "--dots",
                         default=None,
                         nargs="+",
                         help="" )
    args = parser.parse_args( )
    return args

#-------------------------------------------------------------------------------
# custom cmap
#-------------------------------------------------------------------------------

bbcry = {
    'red':
    ( (0.0, 0.0, 0.0),
      (0.25, 0.0, 0.0),
      (0.50, 0.0, 0.0),
      (0.75, 1.0, 1.0),
      (1.0, 1.0, 1.0) ),
    'green':
    ( (0.0, 0.0, 0.0),
      (0.25, 0.0, 0.0),
      (0.50, 1.0, 1.0),
      (0.75, 0.0, 0.0),
      (1.0, 1.0, 1.0) ),
    'blue':
    ( (0.0, 0.0, 0.0),
      (0.25, 1.0, 1.0),
      (0.50, 1.0, 1.0),
      (0.75, 0.0, 0.0),
      (1.0, 0.0, 1.0) ),
}
bbcry = mpl.colors.LinearSegmentedColormap( "bbcry", bbcry, 256 )
pylab.register_cmap( name="bbcry", cmap=bbcry )

#-------------------------------------------------------------------------------
# utility functions
#-------------------------------------------------------------------------------

def subseq( seq, index ):
    """numpy-style slicing and indexing for lists"""
    return [seq[i] for i in index]

def metacolors( values, cmap ):
    found_other = False
    found_none = False
    unique = set( values )
    if c_str_other in unique:
        found_other = True
        unique -= {c_str_other}
    if c_str_none in unique:
        found_none = True
        unique -= {c_str_none}
    if os.path.exists( cmap ):
        cmap = col2dict( cmap, value=1 )
        for k in unique:
            if k not in cmap:
                cmap[k] = c_none_color
        cmap = {l:c for l, c in cmap.items( ) if l in unique}
    else:
        ncol = mu.ncolors( len( unique ), cmap )
        cmap = {}
        for k, c in zip( sorted( unique ), ncol ):
            cmap[k] = c
    if found_other:
        cmap[c_str_other] = c_other_color
    if found_none:
        cmap[c_str_none] = c_none_color
    return cmap

def set_cbar_ticks( ax, lims, poormin=False, poormax=False ):
    vmin, vmax = lims
    tot = vmax - vmin
    scale = 10 ** np.floor( np.log10( tot / 2.0 ) )
    if tot / scale < 5:
        scale /= 2
    if tot / scale > 12:
        scale /= 0.5    
    start = scale * int( vmin / scale )
    ticks = []
    ticklabels = []
    precision = 0
    if scale < 1:
        precision = len( str( scale ).split( "." )[1] )
    while start <= vmax:
        ticks.append( (start - vmin) / tot )
        ticklabels.append( round( start, precision ) )
        start += scale
    # sometimes first tick is 0, then 1 or 10, etc.
    """
    if abs( ticklabels[1] ) > 1:
        ticklabels = map( int, ticklabels )
    """
    ticklabels = map( str, ticklabels )
    # indicate cbar min encapsulates <=
    if poormin:
        ticklabels[0] = u"\u2264" + ticklabels[0]
    # indicate cbar max encapsulates >=
    if poormax:
        ticklabels[-1] = u"\u2265" + ticklabels[-1]
    ax.yaxis.set_ticks( ticks )       
    ax.yaxis.set_ticklabels( ticklabels )
    # avoids weirdness where colors don't extend to bottom of axis
    ax.set_ylim( 0, 1 )
    mu.resize_yticklabels( ax, c_font2 )

def acheck( array, func ):
    n = 0
    d = 0
    for row in array:
        for x in row:
            d += 1
            if func( x ):
                n += 1
    return n, (n / float( d ))

def file_order( path ):
    warn( "reading header order from", path )
    order = {}
    counter = 0
    with open( path ) as fh:
        for line in fh:
            line = line.strip( )
            order[line] = counter
            counter += 1
    return order

def relevel( levels, max_levels=None ):
    counts = Counter( levels )
    counts = sorted( counts, key=lambda x: -counts[x] )
    if max_levels is None or len( counts ) <= max_levels:
        return levels
    else:
        counts = {k for k in counts[0:max_levels]}
        levels = [l if l in counts else c_str_other for l in levels]
        return levels  

def add_dots( axes, df, path ):
    rowmap = {r:i for i, r in enumerate( df.row )}
    colmap = {c:i for i, c in enumerate( df.col )}
    kwargs = {"color":"black", "edgecolor":"none", "s":7}
    with open( path ) as fh:
        for line in fh:
            items = line.strip( ).split( "\t" )
            if items[0] == "#kwargs":
                for item in items[1:]:
                    k, v = item.split( ":" )
                    kwargs[k] = v
            else:
                r, c = items
                if r in rowmap and c in colmap:
                    r = rowmap[r] + 0.5
                    c = colmap[c] + 0.5
                    axes.heatmap.scatter( c, r, **kwargs )
    return [path, kwargs]
                
#-------------------------------------------------------------------------------
# utility classes
#-------------------------------------------------------------------------------

class Dimensions:

    def __init__( self, scale=1 ):
        self.scale       = scale
        self.title_r     = scale * 1
        self.coltree_r   = scale * 3
        self.rowtree_c   = scale * 3
        self.colmeta_r   = scale * 1
        self.rowmeta_c   = scale * 1
        self.colnames_r  = scale * 6
        self.rownames_c  = scale * 12
        self.cbar_c      = scale * 8
        self.cbar_c2     = scale * 1
        self.legend_c    = scale * 8
        self.heat_r      = scale * 16
        self.heat_c      = scale * 24
        self.cbar_extent = 0.5
        self.update( )

    def update( self ):
        self.rmargin    = self.title_r + self.coltree_r + self.colmeta_r
        self.cmargin    = self.rowtree_c + self.rowmeta_c + self.cbar_c
        self.rsize      = self.title_r + self.coltree_r + self.colmeta_r + self.heat_r + self.colnames_r
        self.csize      = self.rowtree_c + self.rowmeta_c + self.heat_c + self.rownames_c \
                          + self.cbar_c + self.legend_c

class DataFrame:

    def __init__( self, path,
                  lastcol=None, lastrow=None,
                  colmeta=None, rowmeta=None,
                  eps_noise=False, ):
        self.tbl = table( path )
        self.bak = self.tbl.copy( )
        # strip / save metadata
        if lastrow is not None:
            self.tbl.head( lastrow, invert=True )
        if lastcol is not None:
            self.tbl.head( lastcol, invert=True, transposed=True )
        self.row = self.tbl.rowheads[:]
        self.col = self.tbl.colheads[:]
        if eps_noise:
            self.tbl.float( )
            self.tbl.apply_entries( lambda x: x + c_eps * random.random( ) )
        self.dat = self.tbl.table2array( )
        # colmetas from file / table
        if colmeta is None:
            self.colmeta = None
            self.colmetaname = None
        else:
            self.colmeta = []
            self.colmetaname = []
            for x in colmeta:
                if os.path.exists( x ):
                    warn( "Loading col metadata from file:", x )
                    temp = col2dict( x, value=1 )
                    self.colmeta.append( [temp.get( k, c_str_none ) for k in self.col] )
                    self.colmetaname.append( path2name( x ) )
                else:
                    temp = self.bak.rowdict( x )
                    self.colmeta.append( [temp.get( k, c_str_none ) for k in self.col] )
                    self.colmetaname.append( x )
        # rowmetas from file / table
        if rowmeta is None:
            self.rowmeta = None
            self.rowmetaname = None
        else:
            self.rowmeta = []
            self.rowmetaname = []
            for x in rowmeta:
                if os.path.exists( x ):
                    warn( "Loading row metadata from file:", x )
                    temp = col2dict( x, value=1 )
                    self.rowmeta.append( [temp.get( k, c_str_none ) for k in self.row] )
                    self.rowmetaname.append( path2name( x ) )
                else:
                    temp = self.bak.coldict( x )
                    self.rowmeta.append( [temp.get( k, c_str_none ) for k in self.row] )
                    self.rowmetaname.append( x )

    def colsort( self, metric, linkage="average" ):
        Z = None
        if metric == "none":
            order = range( len( self.col ) )
        elif metric == "names":
            order = sorted( range( len( self.col ) ), key=lambda i: self.col[i] )
        elif metric == "mean":
            order = sorted( range( len( self.col ) ), key=lambda i: np.mean( self.dat[:, i] ) )
        elif os.path.exists( metric ):
            d = file_order( metric )
            if len( d ) != len( self.col ):
                warn( "dimension mismatch with order in", metric, len( d ), len( self.col ) )
            order = [0 for k in self.col]
            for i, k in enumerate( self.col ):
                if k in d:
                    order[d[k]] = i
                else:
                    warn( "no position for", k, "in", metric )
        elif "metadata" in metric:
            index = 0 if ":" not in metric else ( int( metric.split( ":" )[1] ) - 1 )
            values = self.colmeta[index]
            order = sorted( range( len( values ) ), key=lambda i: values[i] )
        # note: linkage assumes things to cluster = rows; we want cols
        elif metric == "spearman":
            temp = [rankdata( col ) for col in self.dat.transpose( )]
            temp = np.array( temp )
            try:
                Z = sch.linkage( temp, method=linkage, metric="correlation" )
                order = sch.leaves_list( Z )
            except:
                warn( "Spearman clustering failed" )
                Z = None
                order = range( len( self.col ) )
        else:
            Z = sch.linkage( self.dat.transpose(), method=linkage, metric=metric )
            order = sch.leaves_list( Z )
        self.dat = self.dat[:, order]
        self.col = subseq( self.col, order )
        if self.colmeta is not None:
            self.colmeta = [subseq( x, order ) for x in self.colmeta]
        return Z

    def rowsort( self, metric, linkage="average" ):
        Z = None
        if metric == "none":
            order = range( len( self.row ) )
        elif metric == "names":
            order = sorted( range( len( self.row ) ), key=lambda i: self.row[i], reverse=True )
        elif metric == "mean":
            order = sorted( range( len( self.row ) ), key=lambda i: np.mean( self.dat[i] ) )
        elif os.path.exists( metric ):
            d = file_order( metric )
            if len( d ) != len( self.row ):
                warn( "dimension mismatch with order in", metric, len( d ), len( self.row ) )
            order = [0 for k in self.row]
            for i, k in enumerate( self.row ):
                if k in d:
                    order[d[k]] = i
                else:
                    warn( "no position for", k, "in", metric )
        elif "metadata" in metric:
            index = 0 if ":" not in metric else ( int( metric.split( ":" )[1] ) - 1 )
            values = self.rowmeta[index]
            order = sorted( range( len( values ) ), key=lambda i: values[i], reverse=True )
        elif metric == "spearman":
            temp = [rankdata( col ) for col in self.dat.transpose( )]
            temp = np.array( temp )
            try:
                Z = sch.linkage( temp.transpose( ), method=linkage, metric="correlation" )
                order = sch.leaves_list( Z )
            except:
                warn( "Spearman clustering failed" )
                Z = None
                order = range( len( self.row ) )                
        else:
            Z = sch.linkage( self.dat, method=linkage, metric=metric )
            order = sch.leaves_list( Z )
        self.dat = self.dat[order, :]
        self.row = subseq( self.row, order )
        if self.rowmeta is not None:
            self.rowmeta = [subseq( x, order ) for x in self.rowmeta]
        return Z

    def transform( self, method ):
        if method == "none":
            pass
        elif method == "sqrt":
            self.dat = np.sqrt( self.dat )
        elif "log" in method:
            eps = min( [k for row in self.dat for k in row if k > 0] )
            warn( "Applying Laplace smoothing with constant:", eps )
            self.dat = np.log10( self.dat + eps )
            base = int( method.replace( "log", "" ) )
            warn( "Log transforming with base", base )
            self.dat /= np.log10( base )
            
class HeatmapAxes:

    def __init__( self, d ):
        self.d = d
        self.axes = {}
        self.has_colmetaplot = False
        self.has_rowmetaplot = False
        # heatmap
        self.heatmap = plt.subplot2grid(
            (d.rsize, d.csize),
            (d.rmargin, d.cmargin),
            rowspan=d.heat_r,
            colspan=d.heat_c,
            )
        self.axes["heatmap"] = self.heatmap
        # title
        if d.title_r > 0:
            self.title = plt.subplot2grid(
                (d.rsize, d.csize),
                (0, d.cmargin),
                rowspan=d.title_r,
                colspan=d.heat_c,
            )
            self.axes["title"] = self.title                
        # coltree
        if d.coltree_r > 0:
            self.coltree = plt.subplot2grid(
                (d.rsize, d.csize),
                (d.title_r, d.cmargin),
                rowspan=d.coltree_r,
                colspan=d.heat_c,
            )
            self.axes["coltree"] = self.coltree
        # rowtree
        if d.rowtree_c > 0:
            self.rowtree = plt.subplot2grid(
                (d.rsize, d.csize),
                (d.rmargin, d.cbar_c),
                rowspan=d.heat_r,
                colspan=d.rowtree_c,
            )
            self.axes["rowtree"] = self.rowtree
        # colmeta
        if d.colmeta_r > 0:
            self.colmeta = plt.subplot2grid(
                (d.rsize, d.csize),
                (d.title_r + d.coltree_r, d.cmargin),
                rowspan=d.colmeta_r,
                colspan=d.heat_c,
            )
            self.axes["colmeta"] = self.colmeta
        # rowmeta
        if d.rowmeta_c > 0:
            self.rowmeta = plt.subplot2grid(
                (d.rsize, d.csize),
                (d.rmargin, d.cbar_c + d.rowtree_c),
                rowspan=d.heat_r,
                colspan=d.rowmeta_c,
            )
            self.axes["rowmeta"] = self.rowmeta
        # colnames
        if d.colnames_r > 0:
            self.colnames = plt.subplot2grid(
                (d.rsize, d.csize),
                (d.rmargin + d.heat_r, d.cmargin),
                rowspan=d.colnames_r,
                colspan=d.heat_c,
            )
            self.axes["colnames"] = self.colnames
        # rownames
        if d.rownames_c > 0:
            self.rownames = plt.subplot2grid(
                (d.rsize, d.csize),
                (d.rmargin, d.cmargin + d.heat_c),
                rowspan=d.heat_r,
                colspan=d.rownames_c,
            )
            self.axes["rownames"] = self.rownames
        # cbar
        delta = int( d.heat_r * ( 1.0 - d.cbar_extent ) / 2.0 )
        self.cbar = plt.subplot2grid(
            (d.rsize, d.csize),
            (d.rmargin + delta, d.cbar_c - d.cbar_c2),
            rowspan=d.heat_r - 2 * delta,
            colspan=d.cbar_c2,
        )
        self.axes["cbar"] = self.cbar
        # legend
        self.legend = plt.subplot2grid(
            (d.rsize, d.csize),
            (d.rmargin, d.cmargin + d.heat_c + d.rownames_c),
            rowspan=d.heat_r,
            colspan=d.legend_c,
        )
        self.axes["legend"] = self.legend

    def set_title( self, title="Untitled Heatmap" ):
        self.title.text( 0.5, 0.5, title, ha="center", va="center" )
        
    def collabel( self, df, ax_label, scaled=False, path=None ):
        ax_label = "{} (n={:,})".format( ax_label, len( df.col ) )
        # override col names from the table?
        mapping = {}
        if path is not None:
            mapping = col2dict( path, value=1 )
        for l in df.col:
            if l not in mapping:
                mapping[l] = "" if path is not None else l
        if len( df.col ) > c_max_lab and not scaled:
            warn( "Too many column labels." )
            cx = sum( self.colnames.get_xlim( ) ) / 2.0
            cy = sum( self.colnames.get_ylim( ) ) / 2.0
            self.colnames.text( cx, cy, ax_label, size=c_font3, ha="center", va="center" )
        else:
            ypos = self.colnames.get_ylim( )[1]
            self.colnames.set_xlim( 0, len( df.col ) )
            for i, l in enumerate( df.col ):
                self.colnames.text( i + 0.5, ypos, mapping[l],
                                    rotation=90, rotation_mode="anchor",
                                    va="center", ha="right",
                                    size=c_font1, clip_on=False, )
            cx = sum( self.colnames.get_xlim( ) ) / 2.0
            cy = 0
            self.colnames.text( cx, cy, ax_label, size=c_font3, ha="center", va="bottom" )

    def rowlabel( self, df, ax_label, scaled=False, path=None ):
        ax_label = "{} (n={:,})".format( ax_label, len( df.row ) )
        # override row names from the table?
        mapping = {}
        if path is not None:
            mapping = col2dict( path, value=1 )
        for l in df.row:
            if l not in mapping:
                mapping[l] = "" if path is not None else l
        if len( df.row ) > c_max_lab and not scaled:
            warn( "Too many row labels." )
            cx = sum( self.rownames.get_xlim( ) ) / 2.0
            cy = sum( self.rownames.get_ylim( ) ) / 2.0
            self.rownames.text( cx, cy, ax_label, size=c_font3, ha="center", va="center", rotation=90,
                                rotation_mode="anchor" )
        else:
            self.rownames.set_ylim( 0, len( df.row ) )
            for i, l in enumerate( df.row ):
                self.rownames.text( 0, i + 0.5, mapping[l],
                                    va="center", size=c_font1, clip_on=True, )
            cx = self.rownames.get_xlim( )[1]
            cy = sum( self.rownames.get_ylim( ) ) / 2.0
            self.rownames.text( cx, cy, ax_label, size=c_font3, ha="center", va="bottom", rotation=90,
                                rotation_mode="anchor" )

    def get_blocks( self, values, cmap ):
        i = 0
        blocks = []
        n = len( values )
        start = 0
        span = 0
        for i in range( n ):
            span += 1
            if i == n-1 or cmap[values[i]] != cmap[values[i+1]]:
                blocks.append( [start, span, cmap[values[i]]] )
                start = i + 1
                span = 0
        return blocks
                
    def colmetaplot( self, df, cmaps=None, max_levels=None ):
        self.has_colmetaplot = True
        if cmaps is None:
            cmaps = [c_metacmap for k in df.colmeta]
        self.colmeta.set_ylim( 0, len( df.colmeta ) )
        self.colmeta.set_xlim( 0, len( df.colmeta[0] ) )
        for i, levels in enumerate( df.colmeta ):
            levels = relevel( levels, max_levels )
            cmaps[i] = metacolors( levels, cmaps[i] )
            for [start, span, color] in self.get_blocks( levels, cmaps[i] ):
                self.colmeta.bar( start, 1, color=color, width=span, bottom=i, edgecolor="none" )
        self.colmeta.set_yticks( [0.5 + k for k in range( len( df.colmeta ) )] ) 
        self.colmeta.set_yticklabels( df.colmetaname, size=c_font1 )
        mu.user_grid( self.colmeta, h=range( 1, len( cmaps ) ), color="black", zorder=2 )
        mu.hide_yticks( self.colmeta )
        return cmaps

    def rowmetaplot( self, df, cmaps=None, max_levels=None ):
        self.has_rowmetaplot = True
        if cmaps is None:
            cmaps = [c_metacmap for k in df.rowmeta]
        self.rowmeta.set_xlim( 0, len( df.rowmeta ) )
        self.rowmeta.set_ylim( 0, len( df.rowmeta[0] ) )    
        for i, levels in enumerate( df.rowmeta ):
            levels = relevel( levels, max_levels )
            cmaps[i] = metacolors( levels, cmaps[i] )
            for [start, span, color] in self.get_blocks( levels, cmaps[i] ):
                self.rowmeta.barh( start, 1, color=color, height=span, left=i, edgecolor="none" )
        self.rowmeta.set_xticks( [0.5 + k for k in range( len( df.rowmeta ) )] )
        mu.user_grid( self.rowmeta, v=range( 1, len( cmaps ) ), color="black", zorder=2 )
        mu.hide_xticks( self.rowmeta )
        self.rowmeta.set_xticklabels( df.rowmetaname, rotation=90, size=c_font1, \
                                      rotation_mode="anchor", ha="left", va="center" )
        return cmaps
            
    def clean( self ):
        mu.tick_params( self.cbar )
        self.cbar.yaxis.tick_left( )
        self.cbar.yaxis.set_label_position( "left" )
        if "rowmeta" in self.axes:
            self.rowmeta.xaxis.tick_top( )
            mu.hide_xticks( self.rowmeta )
        if "colmeta" in self.axes:
            self.colmeta.yaxis.tick_right( )
            mu.hide_yticks( self.colmeta )
        for name, ax in self.axes.items( ):
            if False:
                x = sum( ax.get_xlim( ) ) / 2.0
                y = sum( ax.get_ylim( ) ) / 2.0
                ax.text( x, y, name )
                continue
            if "rowmeta" not in name or not self.has_rowmetaplot:
                mu.hide_xaxis( ax )
            if "cbar" not in name and "colmeta" not in name:
                mu.hide_yaxis( ax )
            if "tree" in name or "name" in name or "title" in name or "legend" in name:
                mu.hide_border( ax )
        
#-------------------------------------------------------------------------------
# main
#-------------------------------------------------------------------------------

def main( ):
    
    args = get_args( )
    fig = plt.figure( )
    dims = Dimensions( )
    df = DataFrame( args.table,
                    lastcol=args.lastcol, lastrow=args.lastrow,
                    colmeta=args.colmeta, rowmeta=args.rowmeta,
                    eps_noise=args.eps_noise, )

    # force labeling all features
    if args.force_labels:
        global c_max_lab
        c_max_lab = 1e6
    
    # dim overrides
    vscale = 1
    hscale = 1
    if args.colmeta is not None and args.metascale:
        dims.colmeta_r = len( args.colmeta )
    if args.rowmeta is not None and args.metascale:
        dims.rowmeta_c = len( args.rowmeta )
    if args.vscale:
        old = dims.heat_r
        new = int( len( df.row ) / 2.0 ) + len( df.row ) % 2
        new = max( new, 8 )
        dims.heat_r = new
        vscale = new / float( old )
    if args.hscale:
        old = dims.heat_c
        new = int( len( df.col ) / 2.0 ) + len( df.col ) % 2
        dims.heat_c = new
        new = max( new, 12 )
        hscale = new / float( old )
    if args.cbar_extent is not None:
        dims.cbar_extent = args.cbar_extent
    if not args.debug:
        if args.title is None:
            dims.title_r = 0
        # no tree axes if last sort is on 1) file or 2) metadata or 3) nothing
        if os.path.exists( args.colsort[-1] ) \
           or re.search( "none|names|mean|metadata", args.colsort[-1] ):
            dims.coltree_r = 0
        if os.path.exists( args.rowsort[-1] ) \
           or re.search( "none|names|mean|metadata", args.rowsort[-1] ):
            dims.rowtree_c = 0
        if args.colmeta is None:
            dims.colmeta_r = 0
        if args.rowmeta is None:
            dims.rowmeta_c = 0
        if len( df.col ) > c_max_lab and not args.hscale:
            dims.colnames_r = 1
        if len( df.row ) > c_max_lab and not args.vscale:
            dims.rownames_c = 1
    dims.update( )

    # manual overrides
    for o in args.overrides:
        p, v = o.split( ":" )
        v = int( v )
        setattr( dims, p, v )
    dims.update( )

    # define figure
    fig.set_size_inches( args.hstretch * dims.csize * args.grid_inches / dims.scale,
                         args.vstretch * dims.rsize * args.grid_inches / dims.scale )

    # setup axes
    axes = HeatmapAxes( dims )

    # cluster cols
    Z = None
    for metric in args.colsort:
        Z = df.colsort( metric, linkage=args.linkage )
    if Z is not None:
        sch.dendrogram( Z, ax=axes.coltree, \
                        above_threshold_color="0.75", 
                        color_threshold=0, )

    # cluster rows
    Z = None
    for metric in args.rowsort:
        Z = df.rowsort( metric, linkage=args.linkage )
    if Z is not None:
        sch.dendrogram( Z, ax=axes.rowtree, orientation="left", \
                        above_threshold_color="0.75", 
                        color_threshold=0, )

    # apply transform
    df.transform( args.transform )

    # check limits
    poormin = False
    poormax = False
    vmin, vmax = (None, None) if args.limits is None else args.limits
    dmin, dmax = np.min( df.dat ), np.max( df.dat )
    if vmin is None:
        vmin = dmin
    elif dmin < vmin:
        poormin = True
        n, p = acheck( df.dat, lambda x: x < vmin )
        warn( "{} values ({:.2f}%) < vmin ({}), extreme: {}".format( n, 100 * p, vmin, dmin ) )
    if vmax is None:
        vmax = dmax
    elif dmax > vmax:
        poormax = True
        n, p = acheck( df.dat, lambda x: x > vmax )
        warn( "{} values ({:.2f}%) > vmax ({}), extreme: {}".format( n, 100 * p, vmax, dmax ) )

    # add heatmap
    axes.heatmap.set_xlim( 0, len( df.col ) )
    axes.heatmap.set_ylim( 0, len( df.row ) )
    # imshow is similar to pcolorfast, but better centered
    if args.engine == "imshow":
        nr = len( df.row )
        nc = len( df.col )
        kwargs = {"interpolation":"none", "origin":"lower",
                  "aspect":"auto", "extent":[0, nc, 0, nr]}
        pc = axes.heatmap.imshow( df.dat, cmap=args.cmap, vmin=vmin, vmax=vmax, **kwargs )
    # probably no reason to use this
    elif args.engine == "pcolorfast":
        pc = axes.heatmap.pcolorfast( df.dat, cmap=args.cmap, vmin=vmin, vmax=vmax )
    # use this if you want the individual heatmap cells to be editable shapes
    elif args.engine == "pcolormesh":
        pc = axes.heatmap.pcolormesh( df.dat, cmap=args.cmap, vmin=vmin, vmax=vmax )

    # add cmap bar
    fig.colorbar( pc, cax=axes.cbar )
    axes.cbar.set_ylabel( args.units if args.transform == "none" else \
                          "{}( {} )".format( args.transform, args.units ), size=c_font3 )
    set_cbar_ticks( axes.cbar, pc.get_clim( ), poormin=poormin, poormax=poormax )
    
    # add column metadata
    if df.colmeta is not None:
        colmeta_cmaps = axes.colmetaplot( df, args.colmeta_colors, args.max_levels )

    # add row metadata
    if df.rowmeta is not None:
        rowmeta_cmaps = axes.rowmetaplot( df, args.rowmeta_colors, args.max_levels )

    # column transition lines
    if "metadata" in args.colsort[-1]:
        args.colbreaks = args.colsort[-1]
    if args.colbreaks is not None:
        lastsort = args.colbreaks
        index = 0 if ":" not in lastsort else \
                ( int( lastsort.split( ":" )[1] ) - 1 )
        pos = []
        for i, value in enumerate( df.colmeta[index] ):
            if i > 0 and df.colmeta[index][i-1] != value:
                pos.append( i )
        for i in pos:
            mu.vline( axes.colmeta, i, color="black" )
            mu.vline( axes.heatmap, i, color=args.break_color )

    # add row transition lines if ending on a metasort
    if "metadata" in args.rowsort[-1]:
        args.rowbreaks = args.rowsort[-1]
    if args.rowbreaks is not None:
        lastsort = args.rowbreaks
        index = 0 if ":" not in lastsort else \
                ( int( lastsort.split( ":" )[1] ) - 1 )
        pos = []
        for i, value in enumerate( df.rowmeta[index] ):
            if i > 0 and df.rowmeta[index][i-1] != value:
                pos.append( i )
        for i in pos:
            mu.hline( axes.rowmeta, i, color="black" )
            mu.hline( axes.heatmap, i, color=args.break_color )

    # add generic grids
    if "x" in args.grid:
        for i in range( 1, len( df.col ) ):
            mu.vline( axes.heatmap, i, color=args.break_color )
    if "y" in args.grid:
        for i in range( 1, len( df.row ) ):
            mu.hline( axes.heatmap, i, color=args.break_color )
            
    # title
    if args.title is not None:
        axes.set_title( args.title )

    # add dots
    dots_added = []
    if args.dots is not None:
        for p in args.dots:
            dots_added.append( add_dots( axes, df, p ) )

    # legend
    L = mu.Legendizer( axes.legend, vscale=0.7 / vscale )
    # col sort legend
    L.subhead( "Col sort" )
    for m in args.colsort:
        if "metadata" in m:
            i = 0
            if ":" in m:
                i = int( m.split( ":" )[1] ) - 1
            m = "metadata:"+df.colmetaname[i]
        L.element( "_", color="0.75", label=m )
    # row sort legend
    L.subhead( "Row sort" )
    for m in args.rowsort:
        if "metadata" in m:
            i = 0
            if ":" in m:
                i = int( m.split( ":" )[1] ) - 1
            m = "metadata:"+df.rowmetaname[i]
        L.element( "_", color="0.75", label=m )
    # col metadata legend
    levelorder = {c_str_other:1, c_str_none:2}
    if df.colmeta is not None:
        for n, c in zip( df.colmetaname[::-1], colmeta_cmaps[::-1] ):
            L.subhead( n )
            for l in sorted( c, key=lambda x: [levelorder.get( x, 0 ), x] ):
                color = c[l]
                L.element( "s", color=color, label=l )
    # row metadata legend
    if df.rowmeta is not None:
        for n, c in zip( df.rowmetaname[::-1], rowmeta_cmaps[::-1] ):
            L.subhead( n )
            for l in sorted( c, key=lambda x: [levelorder.get( x, 0 ), x] ):
                color = c[l]
                L.element( "s", color=color, label=l )
    if len( dots_added ) > 0:
        L.subhead( "Dots" )
        for p, kwargs in dots_added:
            marker = kwargs.get( "marker", "o" )
            kwargs = {k:v for k, v in kwargs.items( ) if k not in "s marker".split( )}
            L.element( marker, label=path2name( p ), **kwargs )
    # finalize
    L.draw( )
                
    # cleanup
    if args.override_colnames is not "-":
        axes.collabel( df, args.collabel, scaled=args.hscale, path=args.override_colnames )
    if args.override_rownames is not "-":
        axes.rowlabel( df, args.rowlabel, scaled=args.vscale, path=args.override_rownames )
    if not args.debug:
        axes.clean( )
    plt.subplots_adjust( wspace=0.3, hspace=0.3 )
    plt.savefig( args.output, bbox_inches="tight" )

    # logging
    if args.dump_colsort_order:
        with open( args.output+".colsort", "w" ) as fh:
            for item in df.col:
                print >>fh, item
    if args.dump_rowsort_order:
        with open( args.output+".rowsort", "w" ) as fh:
            for item in df.row:
                print >>fh, item
      
if __name__ == "__main__":
    main( )
